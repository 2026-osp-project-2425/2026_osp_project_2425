"""Restore missing local products from Firebase; never write to Firebase.

Place beside app.py and database.py, stop the Flask server, then run:
    python recover_products.py
Existing products and all user/order/review rows remain unchanged.
"""
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def normalize_items(remote):
    if remote is None:
        remote = {}
    if not isinstance(remote, dict):
        raise RuntimeError("Firebase item 데이터 형식을 확인해야 합니다. DB를 변경하지 않았습니다.")
    candidates, problems = [], []
    for firebase_name, payload in sorted(remote.items()):
        if not isinstance(payload, dict):
            problems.append(f"{firebase_name}: 상품 정보 형식이 다름")
            continue
        item = {k: v for k, v in payload.items() if k not in {"local_id", "img_path", "id"}}
        item["name"] = item.get("name") or firebase_name
        if not all(item.get(k) not in (None, "") for k in ("name", "seller_id", "price", "address", "status", "email")):
            problems.append(f"{firebase_name}: 필수 정보가 부족함")
            continue
        local_id = payload.get("local_id")
        if isinstance(local_id, bool) or not str(local_id).isdigit() or not 0 < int(local_id) < 2**63:
            local_id = None
        else:
            local_id = int(local_id)
        if "image" not in item:
            image_path = payload.get("img_path") or ""
            item["image"] = image_path[len("/static/"):] if image_path.startswith("/static/") else ""
        item.setdefault("participants", 0)
        candidates.append((firebase_name, local_id, item))
    return candidates, problems


def missing_items(db_path, remote):
    with sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=rw", uri=True) as connection:
        names = {json.loads(row[0]).get("name") for row in connection.execute("SELECT data FROM products")}
    candidates, problems = normalize_items(remote)
    return [entry for entry in candidates if entry[2]["name"] not in names], problems


def restore_missing(root, remote, db_path=None, selected_keys=None):
    root = Path(root).resolve()
    db_path = Path(db_path or root / "instance" / "market.sqlite3").resolve()
    if not db_path.is_file():
        raise RuntimeError(f"DB 파일이 없습니다. 새 DB는 만들지 않습니다: {db_path}")
    candidates, problems = normalize_items(remote)
    if selected_keys is not None:
        selected_keys = set(selected_keys)
        candidates = [entry for entry in candidates if entry[0] in selected_keys]

    backup_dir = db_path.parent / "recovery_backups"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / (
        "market_before_recovery_" + datetime.now().strftime("%Y%m%d_%H%M%S_")
        + uuid4().hex[:8] + ".sqlite3"
    )
    result = dict(added=[], skipped=[], conflicts=problems, missing_images=[], remapped=[], backup=str(backup_path))
    with sqlite3.connect(db_path.as_uri() + "?mode=rw", uri=True) as connection:
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("DB 무결성 검사에 실패했습니다. 복원을 중단합니다.")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(products)")}
        if not {"id", "data"}.issubset(columns):
            raise RuntimeError("예상한 products 테이블이 없습니다. 복원을 중단합니다.")
        with sqlite3.connect(backup_path) as backup:
            connection.backup(backup)
        print(f"현재 DB 백업 완료: {backup_path}")

        connection.execute("BEGIN IMMEDIATE")
        existing = {
            row[0]: json.loads(row[1])
            for row in connection.execute("SELECT id, data FROM products")
        }
        existing_names = {item.get("name") for item in existing.values()}
        id_counts = Counter(entry[1] for entry in candidates if entry[1] is not None)
        used_ids = set(existing)
        next_id = max(used_ids | set(id_counts), default=0) + 1
        for firebase_name, old_id, item in candidates:
            name = item["name"]
            if name in existing_names:
                result["skipped"].append(name)
                continue
            if old_id is not None and id_counts[old_id] == 1 and old_id not in used_ids:
                local_id = old_id
            else:
                while next_id in used_ids:
                    next_id += 1
                local_id = next_id
                next_id += 1
                result["remapped"].append((name, old_id, local_id))
            connection.execute(
                "INSERT INTO products(id, data) VALUES(?, ?)",
                (local_id, json.dumps(item, ensure_ascii=False))
            )
            existing_names.add(name)
            used_ids.add(local_id)
            result["added"].append(name)
            image = item.get("image")
            if not image or not (root / "static" / image).is_file():
                result["missing_images"].append(name)
    return result


def main():
    root = Path(__file__).resolve().parent
    if not (root / "app.py").is_file() or not (root / "database.py").is_file():
        print("이 파일을 app.py, database.py와 같은 폴더에 넣고 실행해 주세요.")
        return 1
    instance = Path(os.environ.get("OSP_INSTANCE_PATH", root / "instance"))
    db_path = instance / "market.sqlite3"
    if not db_path.is_file():
        print(f"기존 DB를 찾지 못했습니다. 새 DB는 만들지 않습니다: {db_path}")
        return 1
    try:
        # Use the project's credentials and URL. Only read Firebase.
        from database import DBhandler
        from firebase_admin import db
        handler = DBhandler()
        print("Firebase item 데이터를 읽는 중입니다. Firebase 데이터는 수정하지 않습니다.")
        remote = db.reference("item", app=handler.app).get()
        candidates, problems = missing_items(db_path, remote)
        for message in problems:
            print(f"  확인 필요: {message}")
        if not candidates:
            print("Firebase에 현재 DB에 없는 상품이 없습니다. 상품명 기준으로 확인했습니다.")
            return 0
        print("\n현재 DB에 없는 상품입니다. 본인이 복원할 상품을 이름으로 골라 주세요.")
        for index, (key, old_id, item) in enumerate(candidates, 1):
            image = item.get("image")
            photo = "사진 있음" if image and (root / "static" / image).is_file() else "사진 파일 확인 필요"
            print(f"  [{index}] {item['name']} / 기존 번호 {old_id} / {photo}")
        print("\n복원할 선택 번호를 쉼표로 입력하세요. 예: 1,3,4")
        print("전체 상품을 가져오려면 all, 취소하려면 Enter를 입력하세요.")
        try:
            answer = input("복원할 번호: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n취소했습니다. DB를 변경하지 않았습니다.")
            return 0
        if not answer:
            print("취소했습니다. DB를 변경하지 않았습니다.")
            return 0
        if answer.lower() == "all":
            selected = {entry[0] for entry in candidates}
        else:
            try:
                numbers = {int(part.strip()) for part in answer.split(",")}
            except ValueError:
                print("선택 번호 형식이 올바르지 않습니다. DB를 변경하지 않았습니다.")
                return 1
            if not numbers or any(number < 1 or number > len(candidates) for number in numbers):
                print("목록에 없는 선택 번호입니다. DB를 변경하지 않았습니다.")
                return 1
            selected = {candidates[number - 1][0] for number in numbers}
        result = restore_missing(root, remote, db_path, selected_keys=selected)
    except Exception as error:
        print(f"복원 중단 ({type(error).__name__}): {error}")
        print("추가 상품 등록이나 Git 변경 취소를 하지 말고 이 오류 내용을 확인해 주세요.")
        return 1
    print(f"\n복원한 상품: {len(result['added'])}개")
    for name in result["added"]:
        print(f"  복원: {name}")
    for name, old_id, new_id in result["remapped"]:
        print(f"  번호 재배정: {name} / {old_id} -> {new_id}")
    print(f"이미 있어서 유지한 상품: {len(result['skipped'])}개")
    for message in result["conflicts"]:
        print(f"  건너뜀: {message}")
    for name in result["missing_images"]:
        print(f"  사진 파일 확인 필요: {name}")
    if not result["added"]:
        print("새로 복원된 상품이 없습니다. Firebase item에 누락 상품이 남아 있는지 확인해 주세요.")
    print("회원/주문/리뷰 및 기존 상품은 덮어쓰지 않았습니다.")
    print("번호가 재배정된 복원 상품은 예전과 상세 주소가 달라질 수 있습니다.")
    print("이 스크립트는 상품만 복원합니다. Firebase의 local_id와 기존 주문 연결은 변경하지 않습니다.")
    print("확인 후 python app.py로 서버를 다시 실행해 주세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
