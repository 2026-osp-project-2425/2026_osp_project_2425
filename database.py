"""EwhaMarket Firebase Practice 1 + 2.

Run python database.py to check the connection without writing data.
Keep authentication/firebase-key.json on this computer only.
"""
from pathlib import Path
import re

import firebase_admin
from firebase_admin import credentials, db

DATABASE_URL = "https://ewhamarket-2425-default-rtdb.asia-southeast1.firebasedatabase.app/"
ROOT = Path(__file__).resolve().parent


class DuplicateIDError(ValueError):
    pass


class DuplicateItemError(ValueError):
    pass


class DBhandler:
    def __init__(self):
        try:
            self.app = firebase_admin.get_app("ewhamarket")
        except ValueError:
            key_path = ROOT / "authentication" / "firebase-key.json"
            if not key_path.is_file():
                raise FileNotFoundError(
                    "authentication/firebase-key.json 파일을 app.py와 같은 프로젝트 안에 넣어 주세요."
                )
            self.app = firebase_admin.initialize_app(
                credentials.Certificate(str(key_path)),
                {"databaseURL": DATABASE_URL, "httpTimeout": 20},
                name="ewhamarket",
            )

    def check_connection(self):
        return db.reference("/", app=self.app).get(shallow=True)

    @staticmethod
    def validate_item_name(name):
        name = str(name).strip()
        if not name:
            raise ValueError("상품명을 입력해 주세요.")
        if re.search(r"[.#$\[\]/\x00-\x1f\x7f]", name):
            raise ValueError("상품명에는 . # $ [ ] / 및 제어 문자를 사용할 수 없습니다.")
        if len(name.encode("utf-8")) > 768:
            raise ValueError("상품명이 너무 깁니다.")
        return name

    def item_payload(self, data, img_path=None):
        item = {key: value for key, value in data.items() if not key.startswith("_")}
        item["name"] = self.validate_item_name(item.get("name", ""))
        image = item.get("image", "")
        item["img_path"] = img_path if img_path is not None else (
            "/static/" + image if image else ""
        )
        return item

    def insert_item(self, data, img_path=None):
        """Practice 1: /item/상품명 아래 모든 상품 필드를 저장."""
        item = self.item_payload(data, img_path)

        def create(current):
            if current is not None:
                raise DuplicateItemError("이미 등록된 상품명입니다. 다른 상품명을 입력해 주세요.")
            return item

        db.reference("item", app=self.app).child(item["name"]).transaction(create)
        return True

    def update_item(self, previous_name, data):
        """기존 상품 수정과 참여 인원 변경도 Firebase에 반영."""
        previous_name = self.validate_item_name(previous_name)
        item = self.item_payload(data)
        name = item["name"]

        def update(current):
            entries = dict(current or {}) if not isinstance(current, list) else {
                str(i): value for i, value in enumerate(current) if value is not None
            }
            if name != previous_name and name in entries:
                raise DuplicateItemError("이미 등록된 상품명입니다. 다른 상품명을 입력해 주세요.")
            entries.pop(previous_name, None)
            entries[name] = item
            return entries

        db.reference("item", app=self.app).transaction(update)

    @staticmethod
    def validate_username(username):
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            raise ValueError("ID는 영문, 숫자, 밑줄을 사용해 3~30자로 입력해 주세요.")

    def get_user(self, username):
        self.validate_username(username)
        return db.reference("user", app=self.app).child(username).get()

    def insert_user(self, record):
        """Practice 2: ID 중복을 검사하고 허용된 회원 정보와 해시만 저장."""
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

        db.reference("user", app=self.app).child(username).transaction(create)
        return True

    def update_user(self, username, values):
        self.validate_username(username)
        allowed = ("name", "nickname", "email", "student_id", "phone")
        changes = {key: values[key] for key in allowed if key in values}

        def update(current):
            # Firebase 연결 전의 기존 로컬 회원은 자동 이전하지 않습니다.
            if current is None:
                return None
            return dict(current, **changes)

        db.reference("user", app=self.app).child(username).transaction(update)


if __name__ == "__main__":
    try:
        keys = DBhandler().check_connection()
    except Exception as error:
        print(f"연결 실패 ({type(error).__name__}): {error}")
        raise SystemExit(1)
    print("Firebase 연결 성공!")
    print("DB가 비어 있습니다. 정상입니다." if keys is None else "기존 데이터가 있습니다.")
