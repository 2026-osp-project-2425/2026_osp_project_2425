"""Firebase is the shared source for products, accounts and practice images."""
import base64
from datetime import datetime, timezone
from functools import wraps
import os
from pathlib import Path
import re
from uuid import uuid4
import firebase_admin
from firebase_admin import credentials, db

DATABASE_URL = os.environ.get("OSP_DATABASE_URL", "https://ewhamarket-2425-default-rtdb.asia-southeast1.firebasedatabase.app/")
ROOT = Path(__file__).resolve().parent
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

class DuplicateIDError(ValueError):
    pass

class DuplicateItemError(ValueError):
    pass

class SharedStoreError(RuntimeError):
    pass

def shared_operation(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, SharedStoreError):
            raise
        except Exception as error:
            raise SharedStoreError("Firebase 연결에 실패했습니다. 인터넷, 인증키, DATABASE_URL을 확인해 주세요.") from error
    return call

class DBhandler:
    def __init__(self):
        try:
            self.app = firebase_admin.get_app("ewhamarket")
        except ValueError:
            key_path = Path(os.environ.get("OSP_FIREBASE_KEY", ROOT / "authentication" / "firebase-key.json"))
            if not key_path.is_file():
                raise FileNotFoundError("authentication/firebase-key.json 파일을 프로젝트에 넣어 주세요. 인증키는 Git에 올리지 않습니다.")
            self.app = firebase_admin.initialize_app(credentials.Certificate(str(key_path)), {"databaseURL": DATABASE_URL, "httpTimeout": 20}, name="ewhamarket")

    def ref(self, path):
        return db.reference(path, app=self.app)

    @shared_operation
    def check_connection(self):
        return self.ref("/").get(shallow=True)

    @staticmethod
    def valid_key(key):
        return isinstance(key, str) and bool(key) and not re.search(r"[.#$\[\]/\x00-\x1f\x7f]", key)

    @staticmethod
    def validate_item_name(name):
        name = str(name).strip()
        if not name:
            raise ValueError("상품명을 입력해 주세요.")
        if re.search(r"[.#$\[\]/\x00-\x1f\x7f]", name) or len(name.encode("utf-8")) > 768:
            raise ValueError("상품명에는 . # $ [ ] / 및 제어 문자를 사용할 수 없으며 768바이트 이내여야 합니다.")
        return name

    @staticmethod
    def image_path(image):
        if not image:
            return ""
        return "/media/" + image.split("/", 1)[1] if image.startswith("shared/") else "/static/" + image

    def item_payload(self, data, img_path=None):
        item = {key: value for key, value in data.items() if not key.startswith("_") and key not in {"id", "local_id", "product_id"}}
        item["name"] = self.validate_item_name(item.get("name", ""))
        item["img_path"] = img_path if img_path is not None else self.image_path(item.get("image", ""))
        return item

    @staticmethod
    def normalize_item(key, item):
        # The Firebase key is the product name; product_id is immutable.
        # Pre-migration records still use their previous key until migrated.
        product = dict(item, id=str(item.get("product_id") or key))
        product.pop("local_id", None)
        if not product.get("image"):
            path = product.get("img_path") or ""
            if path.startswith("/static/"):
                product["image"] = path[len("/static/"):]
            elif path.startswith("/media/"):
                product["image"] = "shared/" + path[len("/media/"):]
        product.setdefault("participants", 0)
        for field in ("images", "sizes", "colors", "custom_options", "notices"):
            product[field] = product.get(field) or []
        return product

    @shared_operation
    def get_items(self):
        values = self.ref("item").get() or {}
        if not isinstance(values, dict):
            raise SharedStoreError("Firebase item 형식이 올바르지 않습니다.")
        products = [self.normalize_item(key, value) for key, value in values.items() if isinstance(value, dict) and value.get("name")]
        return sorted(products, key=lambda item: (item.get("created_at", ""), item["id"]), reverse=True)

    @shared_operation
    def get_item(self, product_id):
        product_id = str(product_id)
        matches = [item for item in self.get_items() if item["id"] == product_id]
        if len(matches) > 1:
            raise SharedStoreError("중복된 상품 ID가 있습니다. 상품 데이터를 확인해 주세요.")
        return matches[0] if matches else None

    @shared_operation
    def insert_item(self, data, img_path=None):
        item = self.item_payload(data, img_path)
        # UUID is global across computers; the name remains the Firebase key.
        product_id = "p_" + uuid4().hex
        item["product_id"] = product_id
        item.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        item.setdefault("participants", 0)

        def create(current):
            if current is not None:
                raise DuplicateItemError("이미 등록된 상품명입니다. 다른 상품명을 입력해 주세요.")
            return item

        self.ref("item").child(item["name"]).transaction(create)
        return product_id

    def _mutate_item(self, product_id, transform):
        product_id = str(product_id)

        def update(current):
            if not isinstance(current, dict):
                raise ValueError("상품이 없습니다.")
            entries = dict(current)
            matches = [(key, value) for key, value in entries.items()
                       if isinstance(value, dict)
                       and str(value.get("product_id") or key) == product_id]
            if len(matches) != 1:
                raise ValueError("상품 ID가 없거나 중복되어 있습니다.")
            old_key, previous = matches[0]
            item = dict(transform(dict(previous)), product_id=product_id)
            name = self.validate_item_name(item.get("name", ""))
            item["name"] = name
            if name != old_key and name in entries:
                raise DuplicateItemError("이미 등록된 상품명입니다. 다른 상품명을 입력해 주세요.")
            entries.pop(old_key)
            entries[name] = item
            return entries

        # Rename and content changes commit together. Existing product_id stays.
        self.ref("item").transaction(update)

    @shared_operation
    def update_item(self, product_id, data):
        item = self.item_payload(data)
        item.pop("participants", None)
        self._mutate_item(product_id, lambda current: dict(current, **item))

    @shared_operation
    def add_participants(self, product_id, quantity):
        self._mutate_item(product_id, lambda current: dict(
            current, participants=int(current.get("participants", 0)) + int(quantity)
        ))

    @shared_operation
    def upload_image(self, content, filename):
        extension = Path(filename).suffix.lower()
        if extension not in IMAGE_TYPES:
            raise ValueError("PNG, JPG, GIF, WEBP 사진을 선택해 주세요.")
        if not content or len(content) > MAX_IMAGE_BYTES:
            raise ValueError("사진은 파일당 5MB 이하로 선택해 주세요.")
        image_id = uuid4().hex
        self.ref("product_images").child(image_id).set({"content_type": IMAGE_TYPES[extension], "base64": base64.b64encode(content).decode("ascii")})
        return "shared/" + image_id

    @shared_operation
    def get_image(self, image_id):
        if not re.fullmatch(r"[0-9a-f]{32}", image_id):
            return None
        value = self.ref("product_images").child(image_id).get()
        if not isinstance(value, dict):
            return None
        try:
            content = base64.b64decode(value["base64"], validate=True)
            content_type = value["content_type"]
            if content_type not in IMAGE_TYPES.values() or len(content) > MAX_IMAGE_BYTES:
                return None
            return content, content_type
        except (KeyError, ValueError):
            return None

    @shared_operation
    def delete_image(self, image):
        if image.startswith("shared/"):
            image_id = image.split("/", 1)[1]
            if re.fullmatch(r"[0-9a-f]{32}", image_id):
                self.ref("product_images").child(image_id).delete()

    @shared_operation
    def patch_images(self, product_id, image, images=None):
        self._mutate_item(product_id, lambda current: dict(
            current, image=image, images=images or [], img_path=self.image_path(image)
        ))

    @staticmethod
    def validate_username(username):
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            raise ValueError("ID는 영문, 숫자, 밑줄을 사용해 3~30자로 입력해 주세요.")

    @shared_operation
    def get_user(self, username):
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username or ""):
            return None
        value = self.ref("user").child(username).get()
        if not isinstance(value, dict):
            return None
        return dict(value, id=username, username=username, nickname=value.get("nickname") or value.get("name", ""), student_id=value.get("student_id"), phone=value.get("phone", ""))

    @shared_operation
    def insert_user(self, record):
        username = record["username"]
        self.validate_username(username)
        if not record.get("nickname", "").strip():
            raise ValueError("닉네임을 입력해 주세요.")
        if not record.get("password_hash", "").startswith(("scrypt:", "pbkdf2:")):
            raise ValueError("비밀번호는 해시로 변환한 뒤 저장해야 합니다.")
        allowed = ("username", "nickname", "password_hash", "name", "email", "student_id", "phone", "joined_at")
        user = {key: record[key] for key in allowed if key in record}
        user["id"] = username
        def create(current):
            if current is not None:
                raise DuplicateIDError("이미 등록된 ID입니다.")
            return user
        self.ref("user").child(username).transaction(create)
        return True

    @shared_operation
    def update_user(self, username, values):
        self.validate_username(username)
        changes = {key: values[key] for key in ("name", "nickname", "email", "student_id", "phone") if key in values}
        def update(current):
            if not isinstance(current, dict):
                raise ValueError("회원 정보가 없습니다.")
            return dict(current, **changes)
        self.ref("user").child(username).transaction(update)

if __name__ == "__main__":
    try:
        keys = DBhandler().check_connection()
    except Exception as error:
        print(f"연결 실패 ({type(error).__name__}): {error}")
        raise SystemExit(1)
    print("Firebase 연결 성공!")
    print("DB가 비어 있습니다. 정상입니다." if keys is None else "기존 데이터가 있습니다.")
