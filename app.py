"""Open Software Platform Flask practice. Run: python app.py"""
import csv
import io
import json
import math
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database import DBhandler, DuplicateIDError

ROOT = Path(__file__).resolve().parent
DB = DBhandler()
app = Flask(__name__, root_path=str(ROOT))
INSTANCE = Path(os.environ.get("OSP_INSTANCE_PATH", ROOT / "instance"))
INSTANCE.mkdir(parents=True, exist_ok=True)
key_file = INSTANCE / "session.key"
if not key_file.exists():
    key_file.write_text(secrets.token_hex(32))
app.secret_key = os.environ.get("OSP_SECRET_KEY") or key_file.read_text().strip()
app.config.update(MAX_CONTENT_LENGTH=10 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB_PATH = INSTANCE / "market.sqlite3"
UPLOADS = ROOT / "static" / "images" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
LABELS = {"name": "상품명", "seller_id": "판매자 ID", "price": "가격 (원)", "address": "주소", "status": "상품 상태", "email": "이메일", "start_date": "공동구매 시작일", "end_date": "공동구매 종료일", "pickup_datetime": "상품 수령 일시", "target_amount": "목표 금액 (원)", "target_count": "목표 개수", "manufacturer": "제작 업체", "description": "상품 상세 설명", "category": "카테고리", "chat_url": "오픈채팅 링크"}
STATUS_LABELS = {"new": "새 상품", "lnew": "새것에 가까움", "used": "중고"}
WEEKDAYS = "월화수목금토일"
CATEGORIES = ["생활 · 패션", "식품", "기타"]
RATING_LABELS = {5: "아주 만족해요", 4: "만족해요", 3: "보통이에요", 2: "아쉬워요", 1: "불만족해요"}
EMAIL_PATTERN = r"[^\s@]+@[^\s@]+\.[^\s@]+"
CHAT_PATTERN = r"https://open\.kakao\.com/\S+"
OPTION_CATEGORY = CATEGORIES[0]
HEX_PATTERN = r"#[0-9a-fA-F]{6}"
LIST_SORTS = {"popular": "인기순", "latest": "최신순", "reviews": "리뷰 많은 순", "rating": "평점순"}
MANAGE_TABS = {"info": "상품 정보", "participants": "참여자 관리", "orders": "주문·정산 관리", "reviews": "리뷰 관리"}

def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT NOT NULL, student_id TEXT UNIQUE, phone TEXT, joined_at TEXT);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, username TEXT NOT NULL,
          size TEXT, color TEXT, quantity INTEGER NOT NULL, created_at TEXT NOT NULL);
        """)
        # 학번을 선택 항목으로 바꾸기 전에 만들어진 DB를 새 구조로 옮긴다.
        if any(row["name"] == "student_id" and row["notnull"] for row in db.execute("PRAGMA table_info(users)")):
            db.executescript("""
            ALTER TABLE users RENAME TO users_old;
            CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
              email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT NOT NULL, student_id TEXT UNIQUE, phone TEXT, joined_at TEXT);
            INSERT INTO users(id, username, email, password_hash, name, student_id) SELECT id, username, email, password_hash, name, student_id FROM users_old;
            DROP TABLE users_old;
            """)
        if "nickname" not in {row["name"] for row in db.execute("PRAGMA table_info(users)")}:
            db.execute("ALTER TABLE users ADD COLUMN nickname TEXT NOT NULL DEFAULT ''")
            db.execute("UPDATE users SET nickname=name WHERE nickname=''")
        if db.execute("SELECT count(*) FROM products").fetchone()[0] == 0:
            samples = [
                dict(name="2026 배꽃 나비 학잠", seller_id="seahna", price="36000", address="이화여자대학교 학문관 앞", status="new", email="seller@example.com", start_date="2026-10-01", end_date="2026-10-30", pickup_datetime="2026-10-15T14:00", target_amount="100000", target_count="40", manufacturer="웨체비", description="이화인들과 함께하는 학잠 공동구매입니다. 옵션을 선택하고 참여해 주세요.", category="생활 · 패션", participants=32, image=""),
                dict(name="웨체비 주경바막", seller_id="seahna", price="30000", address="이화여자대학교 학문관 403호 앞", status="new", email="seller@example.com", start_date="2026-10-01", end_date="2026-10-30", pickup_datetime="2026-10-15T14:00", target_amount="100000", target_count="40", manufacturer="웨체비", description="겨울 통학에 활용할 수 있는 바람막이 공동구매입니다.", category="생활 · 패션", participants=32, image=""),
            ]
            for item in samples:
                db.execute("INSERT INTO products(data) VALUES(?)", (json.dumps(item, ensure_ascii=False),))
        if db.execute("SELECT count(*) FROM reviews").fetchone()[0] == 0:
            for title, author in [("주경바막 최고", "doeun_24"), ("따뜻하고 편해요", "ewha_25")]:
                data = dict(product_id=2, title=title, author=author, rating=5, description="주경바막 완전 겨울통학 필수템! 따뜻하고 자수도 예뻐요.", date="2026.10.09", image="", size="M", color="블랙")
                db.execute("INSERT INTO reviews(data) VALUES(?)", (json.dumps(data, ensure_ascii=False),))

init_db()

def records(table):
    with connect() as db:
        rows = db.execute(f"SELECT id, data FROM {table} ORDER BY id DESC").fetchall()
    return [dict(json.loads(row["data"]), id=row["id"]) for row in rows]

def product_by_id(product_id):
    for item in records("products"):
        if item["id"] == product_id:
            return item
    abort(404)

def save_product(product):
    data = {key: value for key, value in product.items() if key != "id"}
    with connect() as db:
        previous = db.execute("SELECT data FROM products WHERE id=?", (product["id"],)).fetchone()
        previous_name = json.loads(previous["data"])["name"]
        db.execute("UPDATE products SET data=? WHERE id=?", (json.dumps(data, ensure_ascii=False), product["id"]))
        # 상품명 아래 Firebase 데이터도 함께 수정합니다.
        DB.update_item(previous_name, dict(data, local_id=product["id"]))

def owned_product(product_id):
    product = product_by_id(product_id)
    if not session.get("user") or product["seller_id"] != session["user"]["username"]:
        abort(403)
    return product

def order_rows(where, params):
    with connect() as db:
        rows = db.execute(f"SELECT orders.*, users.name FROM orders LEFT JOIN users ON users.username = orders.username WHERE {where} ORDER BY orders.id DESC", params).fetchall()
    return [dict(row) for row in rows]

def my_order(order_id):
    if not session.get("user"):
        abort(403)
    rows = order_rows("orders.id=? AND orders.username=?", (order_id, session["user"]["username"]))
    if not rows:
        abort(404)
    return rows[0]

def order_option(order):
    return " / ".join(value for value in (order.get("color"), order.get("size")) if value)

def option_summary(orders):
    summary = {}
    for order in orders:
        entry = summary.setdefault(order_option(order), dict(option=order_option(order) or "옵션 없음", orders=0, quantity=0))
        entry["orders"] += 1
        entry["quantity"] += order["quantity"]
    return sorted(summary.values(), key=lambda entry: entry["quantity"], reverse=True)

def image_upload(field="file_input", required=False):
    image = request.files.get(field)
    if not image or not image.filename:
        if required:
            raise ValueError("상품 사진을 선택해 주세요.")
        return "", ""
    extension = Path(image.filename).suffix.lower()
    if extension not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("PNG, JPG, GIF, WEBP 사진 파일을 선택해 주세요.")
    name = uuid4().hex + extension
    image.save(UPLOADS / name)
    return "images/uploads/" + name, image.filename

@app.context_processor
def shared_context():
    return dict(user=session.get("user"), cart_count=sum(int(x["quantity"]) for x in session.get("cart", [])), labels=LABELS, status_labels=STATUS_LABELS, categories=CATEGORIES, option_category=OPTION_CATEGORY, rating_labels=RATING_LABELS)

@app.template_filter("won")
def won(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"

def parse_datetime(value, pattern):
    try:
        return datetime.strptime(value or "", pattern)
    except ValueError:
        return None

def days_left(product):
    end = parse_datetime(product.get("end_date"), "%Y-%m-%d")
    return (end.date() - datetime.now().date()).days if end else None

@app.template_filter("kdate")
def kdate(value):
    parsed = parse_datetime(value, "%Y-%m-%d")
    return f"{parsed:%Y.%m.%d} ({WEEKDAYS[parsed.weekday()]})" if parsed else ""

@app.template_filter("order_number")
def order_number(order):
    return f"EW-{order['created_at'].replace('.', '')}-{order['id']:04d}"

@app.template_filter("option")
def option_filter(order):
    return order_option(order)

@app.template_filter("funding")
def funding(product):
    left = days_left(product)
    target = int(product.get("target_count") or 0)
    participants = product.get("participants", 0)
    closed = left is not None and left < 0
    reached = participants >= target
    pickup = parse_datetime(product.get("pickup_datetime"), "%Y-%m-%dT%H:%M")
    return dict(
        left=left,
        closed=closed,
        target=target,
        participants=participants,
        progress=min(100, participants * 100 // target) if target else 0,
        remaining=max(0, target - participants),
        confirmed=closed and reached,
        cancelled=closed and not reached,
        # 수령 일시가 없으면 공동구매 확정과 동시에 수령한 것으로 본다.
        received=closed and reached and (pickup is None or pickup <= datetime.now()),
        pickup=f"{pickup:%Y.%m.%d}" if pickup else "",
    )

def stages(product, last_step, finished=False):
    """진행 단계 표시용. 배송 정보는 따로 저장하지 않으므로 수령 일시를 기준으로 나눈다."""
    state = funding(product)
    if state["cancelled"]:
        return None
    start = parse_datetime(product.get("start_date"), "%Y-%m-%d")
    end = parse_datetime(product.get("end_date"), "%Y-%m-%d")
    pickup = parse_datetime(product.get("pickup_datetime"), "%Y-%m-%dT%H:%M")
    planned = "" if state["closed"] else " 예정"
    steps = [
        ("상품 등록", f"{start:%m.%d}" if start else ""),
        ("모집 진행", f"{start:%m.%d}~{end:%m.%d}" if start and end else (f"~{end:%m.%d}" if end else "")),
        ("구매 확정", f"{end + timedelta(days=1):%m.%d}{planned}" if end else ""),
        ("수령", f"{pickup:%m.%d}{'' if state['received'] else ' 예정'}" if pickup else "일정 미정"),
        last_step,
    ]
    current = 1 if not state["closed"] else 3 if not state["received"] else 5 if finished else 4
    return [dict(label=label, note=note, state="done" if index < current else "cur" if index == current else "") for index, (label, note) in enumerate(steps)]

def review_stats(reviews):
    stats = {}
    for review in reviews:
        stats.setdefault(review["product_id"], []).append(review["rating"])
    return {key: dict(count=len(scores), average=sum(scores) / len(scores)) for key, scores in stats.items()}

def page(template, title, active="", **context):
    return render_template(template, page_title=title, active=active, css_file=template.replace(".html", ".css"), **context)

def product_list_context():
    all_products = records("products")
    items = all_products[:]
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    if query:
        items = [p for p in items if query.casefold() in (p["name"] + " " + p.get("manufacturer", "") + " " + p["seller_id"]).casefold()]
    if category:
        items = [p for p in items if p.get("category") == category]
    status = "closed" if request.args.get("status") == "closed" else "open"
    closed_items = [p for p in items if funding(p)["closed"]]
    open_items = [p for p in items if not funding(p)["closed"]]
    items = closed_items if status == "closed" else open_items
    sort = request.args.get("sort") if request.args.get("sort") in LIST_SORTS else "popular"
    stats = review_stats(records("reviews"))
    # 최신순은 records의 기본 순서를 그대로 쓰고, 나머지는 안정 정렬이라 같은 값이면 최신순이 유지된다.
    if sort == "popular":
        items.sort(key=lambda p: p.get("participants", 0), reverse=True)
    elif sort == "reviews":
        items.sort(key=lambda p: stats.get(p["id"], {}).get("count", 0), reverse=True)
    elif sort == "rating":
        items.sort(key=lambda p: (stats.get(p["id"], {}).get("average", 0), stats.get(p["id"], {}).get("count", 0)), reverse=True)
    pages = max(1, math.ceil(len(items) / 4))
    number = min(max(request.args.get("page", 1, type=int), 1), pages)
    return dict(products=items[(number-1)*4:number*4], product_count=len(items), open_count=len(open_items), closed_count=len(closed_items), status=status, review_stats=stats, ranking=sorted(all_products, key=lambda p: p.get("participants", 0), reverse=True)[:3], current_page=number, pages=pages, query=query, category=category, sort=sort, sorts=LIST_SORTS)

@app.route("/")
def hello():
    return page("index.html", "상품 목록", "list", **product_list_context())

@app.route("/list")
def view_list():
    return page("product_list.html", "상품 목록", "list", **product_list_context())

@app.route("/reg_items")
def reg_item():
    return page("product_registration.html", "상품 등록", "registration")

def option_lines(text):
    # 입력 칸은 한 줄에 옵션 하나씩 담아 보낸다. 빈 줄과 중복은 버린다.
    names = []
    for line in text.splitlines():
        line = line.strip()[:40]
        if line and line not in names:
            names.append(line)
    return names[:20]

def read_options(data):
    fashion = data.get("category", OPTION_CATEGORY) == OPTION_CATEGORY
    sizes = option_lines(data.get("sizes", "")) if fashion and data.get("size_enabled") else []
    colors = []
    if fashion and data.get("color_enabled"):
        for line in option_lines(data.get("colors", "")):
            name, _, hex_code = line.rpartition("|") if "|" in line else (line, "", "")
            name = name.strip()
            if name and name not in [c["name"] for c in colors]:
                colors.append(dict(name=name, hex=hex_code if re.fullmatch(HEX_PATTERN, hex_code) else ""))
    data["sizes"], data["colors"] = sizes, colors
    if fashion and data.get("size_enabled") and not sizes:
        raise ValueError("사이즈를 하나 이상 입력하거나 '사이즈 선택 받기'를 꺼 주세요.")
    if fashion and data.get("color_enabled") and not colors:
        raise ValueError("색상을 하나 이상 입력하거나 '색상 선택 받기'를 꺼 주세요.")

def chosen_options(product, form):
    # 진행자가 등록한 옵션만 받고, 옵션이 없는 상품은 빈 값으로 기록한다.
    size, color = form.get("size", ""), form.get("color", "")
    if product.get("sizes") and size not in product["sizes"]:
        raise ValueError("사이즈를 선택해 주세요.")
    if product.get("colors") and color not in [c["name"] for c in product["colors"]]:
        raise ValueError("색상을 선택해 주세요.")
    return dict(size=size if product.get("sizes") else "", color=color if product.get("colors") else "")

def validate_product(data):
    data["name"] = DB.validate_item_name(data.get("name", ""))
    read_options(data)
    for key in ("name", "seller_id", "price", "address", "status", "email"):
        if not data.get(key, "").strip():
            raise ValueError(f"{LABELS[key]}을 입력해 주세요.")
    if not data["price"].isdigit() or int(data["price"]) < 0:
        raise ValueError("가격은 0 이상의 정수로 입력해 주세요.")
    if data["status"] not in STATUS_LABELS:
        raise ValueError("상품 상태를 확인해 주세요.")
    if data.get("category", CATEGORIES[0]) not in CATEGORIES:
        raise ValueError("카테고리를 확인해 주세요.")
    if not re.fullmatch(EMAIL_PATTERN, data["email"]):
        raise ValueError("이메일 형식을 확인해 주세요.")
    data["chat_url"] = data.get("chat_url", "").strip()
    if data["chat_url"] and not re.fullmatch(CHAT_PATTERN, data["chat_url"]):
        raise ValueError("오픈채팅 링크는 https://open.kakao.com/ 으로 시작하는 주소로 입력해 주세요.")
    if data.get("target_count") and (not data["target_count"].isdigit() or int(data["target_count"]) < 1):
        raise ValueError(f"{LABELS['target_count']}를 확인해 주세요.")
    if data.get("start_date") and data.get("end_date") and data["end_date"] < data["start_date"]:
        raise ValueError("종료일은 시작일 이후로 지정해 주세요.")
    data["target_amount"] = str(int(data["price"]) * int(data["target_count"])) if data.get("target_count") else ""
    # 켜짐 여부는 다시 그릴 때만 쓰므로 검사가 끝나면 저장하지 않는다.
    data.pop("size_enabled", None)
    data.pop("color_enabled", None)

@app.route("/submit_item_post", methods=["POST"])
def reg_item_submit_post():
    data = request.form.to_dict()
    if session.get("user"):
        data["seller_id"] = session["user"]["username"]
    image = ""
    try:
        validate_product(data)
        image, filename = image_upload(required=True)
        item = dict(data, image=image, participants=0)
        with connect() as db:
            product_id = db.execute("INSERT INTO products(data) VALUES(?)", (json.dumps(item, ensure_ascii=False),)).lastrowid
            # Practice 1: POST 요청으로 받은 모든 입력값과 사진 경로를 저장합니다.
            DB.insert_item(dict(item, local_id=product_id), img_path=url_for("static", filename=image))
    except ValueError as error:
        if image:
            (ROOT / "static" / image).unlink(missing_ok=True)
        return page("error.html", "입력 확인", "registration", message=str(error)), 400
    except Exception:
        if image:
            (ROOT / "static" / image).unlink(missing_ok=True)
        app.logger.exception("Firebase product save failed")
        return page("error.html", "저장 실패", "registration", message="Firebase에 상품을 저장하지 못했습니다. 연결을 확인하고 다시 시도해 주세요."), 503
    return page("result.html", "상품 등록 결과", "registration", data=data, original_filename=filename, img_path=url_for("static", filename=image), product_id=product_id)

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_item(product_id):
    product = owned_product(product_id)
    if request.method == "POST":
        data = dict(request.form.to_dict(), seller_id=product["seller_id"])
        try:
            validate_product(data)
            image, _ = image_upload()
        except ValueError as error:
            flash(str(error), "error")
            return page("product_registration.html", "상품 정보 수정", "account", product=dict(product, **data)), 400
        product.update(data)
        if image:
            product["image"] = image
        try:
            save_product(product)
        except ValueError as error:
            flash(str(error), "error")
            return page("product_registration.html", "상품 정보 수정", "account", product=product), 400
        except Exception:
            app.logger.exception("Firebase product update failed")
            return page("error.html", "저장 실패", message="Firebase 연결을 확인하고 다시 시도해 주세요."), 503
        flash("상품 정보를 수정했습니다.", "success")
        return redirect(url_for("manage", product_id=product_id, tab="info"))
    return page("product_registration.html", "상품 정보 수정", "account", product=product)

def product_detail_context(product):
    end = parse_datetime(product.get("end_date"), "%Y-%m-%d")
    pickup = parse_datetime(product.get("pickup_datetime"), "%Y-%m-%dT%H:%M")
    state = funding(product)
    return dict(
        days_left=state["left"],
        deadline=f"{end.month}월 {end.day}일" if end else "",
        pickup_text=f"{pickup:%Y.%m.%d} ({WEEKDAYS[pickup.weekday()]}) {pickup:%H:%M}" if pickup else "일정 미정",
        target=state["target"],
        progress=state["progress"],
        remaining=state["remaining"],
    )

@app.route("/product_detail")
def product_detail():
    product = product_by_id(request.args.get("id", 1, type=int))
    return page("product_detail.html", "상품 상세", "list", product=product, **product_detail_context(product))

@app.route("/review")
def view_review():
    reviews = records("reviews")
    product_id = request.args.get("product_id", type=int)
    product = product_by_id(product_id) if product_id else None
    if product:
        reviews = [r for r in reviews if r["product_id"] == product_id]
    review_count = len(reviews)
    average = sum(r["rating"] for r in reviews) / review_count if reviews else 0
    distribution = [(score, sum(r["rating"] == score for r in reviews)) for score in range(5, 0, -1)]
    sort = request.args.get("sort", "latest")
    if sort == "rating":
        reviews.sort(key=lambda r: r["rating"], reverse=True)
    elif sort == "photo":
        reviews = [r for r in reviews if r.get("image")]
    products = {p["id"]: p for p in records("products")}
    pages = max(1, math.ceil(len(reviews) / 4))
    number = min(max(request.args.get("page", 1, type=int), 1), pages)
    return page("review_list.html", "리뷰 목록", "review", reviews=reviews[(number-1)*4:number*4], listed_count=len(reviews), products=products, product=product, review_count=review_count, average=average, distribution=distribution, sort=sort, current_page=number, pages=pages, product_id=product_id)

@app.route("/review_detail")
def review_detail():
    review_id = request.args.get("id", 1, type=int)
    review = next((r for r in records("reviews") if r["id"] == review_id), None)
    if not review:
        abort(404)
    return page("review_detail.html", "리뷰 상세", "review", review=review, product=product_by_id(review["product_id"]))

def latest_order(product_id):
    if not session.get("user"):
        return None
    return next(iter(order_rows("orders.product_id=? AND orders.username=?", (product_id, session["user"]["username"]))), None)

@app.route("/reg_reviews", methods=["GET", "POST"])
def reg_review():
    products = records("products")
    product_id = request.values.get("product_id", 2, type=int)
    product = product_by_id(product_id)
    order = latest_order(product_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        rating = request.form.get("rating", 5, type=int)
        if not title or not description or rating not in range(1, 6):
            flash("제목, 내용, 1~5점 평점을 입력해 주세요.", "error")
        else:
            try:
                image, _ = image_upload()
            except ValueError as error:
                flash(str(error), "error")
            else:
                data = dict(product_id=product_id, title=title, description=description, rating=rating, author=session.get("user", {}).get("username", "User"), date=datetime.now().strftime("%Y.%m.%d"), image=image, size=order["size"] if order else "", color=order["color"] if order else "")
                with connect() as db:
                    review_id = db.execute("INSERT INTO reviews(data) VALUES(?)", (json.dumps(data, ensure_ascii=False),)).lastrowid
                flash("리뷰가 등록되었습니다.", "success")
                return redirect(url_for("review_detail", id=review_id))
    return page("review_writing.html", "리뷰 작성", "writing", products=products, product=product, order=order)

@app.route("/cart")
def cart():
    entries = []
    for item in session.get("cart", []):
        p = product_by_id(item["product_id"])
        entries.append(dict(item, product=p, subtotal=int(p["price"]) * int(item["quantity"])))
    return page("cart.html", "장바구니", "cart", entries=entries, total=sum(x["subtotal"] for x in entries))

@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", type=int)
    product = product_by_id(product_id)
    if funding(product)["closed"]:
        flash("마감된 공동구매는 장바구니에 담을 수 없어요.", "error")
        return redirect(url_for("product_detail", id=product_id))
    try:
        options = chosen_options(product, request.form)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("product_detail", id=product_id))
    quantity = max(1, min(request.form.get("quantity", 1, type=int), 99))
    entries = session.get("cart", [])
    match = next((x for x in entries if x["product_id"] == product_id and x["size"] == options["size"] and x["color"] == options["color"]), None)
    if match:
        match["quantity"] = min(99, match["quantity"] + quantity)
    else:
        entries.append(dict(product_id=product_id, quantity=quantity, **options))
    session["cart"] = entries
    flash("장바구니에 담았습니다.", "success")
    return redirect(url_for("cart"))

@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    entries = session.get("cart", [])
    index = request.form.get("index", -1, type=int)
    if 0 <= index < len(entries):
        entries.pop(index)
    session["cart"] = entries
    return redirect(url_for("cart"))

@app.route("/participate", methods=["POST"])
def participate():
    single_id = request.form.get("product_id", type=int)
    back = url_for("product_detail", id=single_id) if single_id else url_for("cart")
    if not session.get("user"):
        flash("로그인 후 공동구매에 참여할 수 있어요.", "error")
        return redirect(url_for("login", next=back))
    if single_id:
        try:
            options = chosen_options(product_by_id(single_id), request.form)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(back)
        entries = [dict(product_id=single_id, quantity=max(1, min(request.form.get("quantity", 1, type=int), 99)), **options)]
    else:
        entries = session.get("cart", [])
    if not entries:
        flash("참여할 상품을 먼저 담아 주세요.", "error")
        return redirect(url_for("cart"))
    products = [product_by_id(entry["product_id"]) for entry in entries]
    closed = [p["name"] for p in products if funding(p)["closed"]]
    if closed:
        flash(f"마감된 공동구매에는 참여할 수 없어요: {', '.join(closed)}", "error")
        return redirect(back)
    for entry, p in zip(entries, products):
        with connect() as db:
            order_id = db.execute("INSERT INTO orders(product_id, username, size, color, quantity, created_at) VALUES(?,?,?,?,?,?)", (p["id"], session["user"]["username"], entry["size"], entry["color"], entry["quantity"], datetime.now().strftime("%Y.%m.%d"))).lastrowid
        p["participants"] = p.get("participants", 0) + entry["quantity"]
        save_product(p)
    if single_id:
        return redirect(url_for("order_done", order_id=order_id))
    session["cart"] = []
    flash(f"{len(entries)}개 상품의 공동구매 참여가 확정됐어요. 실제 결제는 진행되지 않습니다.", "success")
    return redirect(url_for("account"))

@app.route("/order_done/<int:order_id>")
def order_done(order_id):
    order = my_order(order_id)
    product = product_by_id(order["product_id"])
    return page("order_done.html", "구매 확정 완료", "", order=order, product=product, **product_detail_context(product))

@app.route("/joined/<int:order_id>")
def joined_detail(order_id):
    order = my_order(order_id)
    product = product_by_id(order["product_id"])
    state = funding(product)
    review = next((r for r in records("reviews") if r["product_id"] == product["id"] and r["author"] == order["username"]), None)
    tab = request.args.get("tab") if request.args.get("tab") in ("people", "contact") else "notice"
    title = "진행 중 상품 상세" if not state["closed"] else "참여 상품 상세"
    return page("joined_detail.html", title, "account", order=order, product=product, state=state, review=review, tab=tab, steps=stages(product, ("리뷰 작성", "수령 후"), finished=bool(review)), options=option_summary(order_rows("orders.product_id=?", (product["id"],))), **product_detail_context(product))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        values = {key: request.form.get(key, "").strip() for key in ("username", "email", "nickname", "name", "student_id", "phone")}
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirm", "")
        error = None
        if not all(values[key] for key in ("username", "email", "nickname", "name")) or not password or not confirmation:
            error = "모든 필수 항목을 입력해 주세요."
        elif not re.fullmatch(r"[A-Za-z0-9_]{3,30}", values["username"]):
            error = "ID는 영문, 숫자, 밑줄을 사용해 3~30자로 입력해 주세요."
        elif len(values["nickname"]) > 30:
            error = "닉네임은 30자 이하로 입력해 주세요."
        elif not re.fullmatch(EMAIL_PATTERN, values["email"]):
            error = "이메일 형식을 확인해 주세요."
        elif values["student_id"] and not values["student_id"].isdigit():
            error = "학번은 숫자로 입력해 주세요."
        elif len(password) < 10 or not all(re.search(pattern, password) for pattern in (r"[A-Z]", r"[a-z]", r"[0-9]")):
            error = "비밀번호는 대문자, 소문자, 숫자를 포함해 10자 이상으로 입력해 주세요."
        elif password != confirmation:
            error = "비밀번호 확인이 일치하지 않습니다."
        if error:
            flash(error, "error")
        else:
            record = dict(values, password_hash=generate_password_hash(password),
                          student_id=values["student_id"] or None,
                          joined_at=datetime.now().strftime("%Y.%m.%d"))
            try:
                with connect() as db:
                    db.execute("INSERT INTO users(username,email,password_hash,name,student_id,phone,joined_at,nickname) VALUES(?,?,?,?,?,?,?,?)",
                               tuple(record[key] for key in ("username", "email", "password_hash", "name", "student_id", "phone", "joined_at", "nickname")))
                    # Practice 2: /user/ID 아래 저장. Firebase에서도 중복을 막습니다.
                    DB.insert_user(record)
            except (sqlite3.IntegrityError, DuplicateIDError):
                flash("이미 등록된 ID, 이메일 또는 학번입니다.", "error")
            except Exception:
                app.logger.exception("Firebase signup failed")
                return page("error.html", "저장 실패", "login", message="Firebase에 회원 정보를 저장하지 못했습니다. 연결을 확인하고 다시 시도해 주세요."), 503
            else:
                flash("회원가입이 완료되었습니다. 로그인해 주세요.", "success")
                return redirect(url_for("login"))
    return page("signup.html", "회원가입", "login")

@app.route("/check_id")
def check_id():
    username = request.args.get("username", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
        return dict(available=False, message="영문, 숫자, 밑줄 3~30자로 입력해 주세요.")
    with connect() as db:
        local_taken = bool(db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone())
    try:
        taken = local_taken or DB.get_user(username) is not None
    except Exception:
        app.logger.exception("Firebase ID check failed")
        return dict(available=False, message="중복 확인에 실패했습니다. 잠시 후 다시 시도해 주세요."), 503
    return dict(available=not taken, message="사용할 수 있는 아이디예요" if not taken else "사용할 수 없는 아이디예요")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with connect() as db:
            user = db.execute("SELECT * FROM users WHERE username=?", (request.form.get("username", ""),)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session["user"] = {key: user[key] for key in ("username", "name", "nickname", "email", "student_id")}
            flash("로그인되었습니다.", "success")
            # 다른 사이트로 넘어가지 않도록 이 사이트 안의 경로만 따른다.
            next_url = request.form.get("next", "")
            if not next_url.startswith("/") or next_url.startswith(("//", "/\\")):
                next_url = url_for("account")
            return redirect(next_url)
        flash("ID 또는 비밀번호를 확인해 주세요.", "error")
    return page("login.html", "로그인", "login")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("login"))

def current_profile():
    if not session.get("user"):
        return None
    with connect() as db:
        return db.execute("SELECT * FROM users WHERE username=?", (session["user"]["username"],)).fetchone()

@app.route("/account")
def account():
    profile = current_profile()
    if not profile:
        return page("account.html", "계정정보", "account", profile=None)
    products = {p["id"]: p for p in records("products")}
    tab = "hosted" if request.args.get("tab") == "hosted" else "joined"
    if tab == "joined":
        my_reviews = {r["product_id"]: r for r in reversed(records("reviews")) if r["author"] == profile["username"]}
        items = [dict(order, product=products[order["product_id"]], state=funding(products[order["product_id"]]), review=my_reviews.get(order["product_id"])) for order in order_rows("orders.username=?", (profile["username"],)) if order["product_id"] in products]
    else:
        stats = review_stats(records("reviews"))
        items = [dict(product=p, state=funding(p), reviews=stats.get(p["id"], {}).get("count", 0)) for p in products.values() if p["seller_id"] == profile["username"]]
    status = request.args.get("status") if request.args.get("status") in ("open", "closed") else "all"
    if status != "all":
        items = [item for item in items if item["state"]["closed"] == (status == "closed")]
    return page("account.html", "마이페이지", "account", profile=profile, tab=tab, items=items, status=status)

@app.route("/account/edit", methods=["GET", "POST"])
def account_edit():
    profile = current_profile()
    if not profile:
        return redirect(url_for("login"))
    if request.method == "POST":
        values = {key: request.form.get(key, "").strip() for key in ("name", "email", "student_id", "phone", "nickname")}
        if not values["name"] or not values["nickname"] or len(values["nickname"]) > 30 or not re.fullmatch(EMAIL_PATTERN, values["email"]):
            flash("이름, 닉네임(30자 이하), 이메일을 확인해 주세요.", "error")
        elif values["student_id"] and not values["student_id"].isdigit():
            flash("학번은 숫자로 입력해 주세요.", "error")
        else:
            try:
                with connect() as db:
                    db.execute("UPDATE users SET name=?, email=?, student_id=?, phone=?, nickname=? WHERE id=?", (values["name"], values["email"], values["student_id"] or None, values["phone"], values["nickname"], profile["id"]))
                    DB.update_user(profile["username"], dict(values, student_id=values["student_id"] or None))
            except sqlite3.IntegrityError:
                flash("이미 등록된 이메일 또는 학번입니다.", "error")
            except Exception:
                app.logger.exception("Firebase profile update failed")
                return page("error.html", "저장 실패", message="Firebase 연결을 확인하고 다시 시도해 주세요."), 503
            else:
                session["user"] = dict(session["user"], name=values["name"], nickname=values["nickname"], email=values["email"], student_id=values["student_id"] or None)
                flash("계정 정보를 수정했습니다.", "success")
                return redirect(url_for("account"))
    return page("account_edit.html", "정보 수정", "account", profile=profile)

@app.route("/manage/<int:product_id>")
def manage(product_id):
    product = owned_product(product_id)
    tab = request.args.get("tab") if request.args.get("tab") in (*MANAGE_TABS, "notice") else "participants"
    orders = order_rows("orders.product_id=?", (product_id,))
    query = request.args.get("q", "").strip()
    listed = [o for o in orders if query.casefold() in f"{o['name'] or ''} {o['username']}".casefold()] if query else orders
    pages = max(1, math.ceil(len(listed) / 5))
    number = min(max(request.args.get("page", 1, type=int), 1), pages)
    reviews = [r for r in records("reviews") if r["product_id"] == product_id]
    notices = sorted(product.get("notices", []), key=lambda n: (n["important"], n["id"]), reverse=True)
    return page("manage.html", "공동구매 관리", "account", product=product, state=funding(product), tab=tab, tabs=MANAGE_TABS, orders=orders, listed=listed[(number-1)*5:number*5], listed_count=len(listed), query=query, current_page=number, pages=pages, options=option_summary(orders), quantity=sum(o["quantity"] for o in orders), reviews=reviews, notices=notices, steps=stages(product, ("종료", ""), finished=True), **product_detail_context(product))

@app.route("/manage/<int:product_id>/notices", methods=["POST"])
def manage_notices(product_id):
    product = owned_product(product_id)
    notices = product.get("notices", [])
    delete_id = request.form.get("delete", type=int)
    title = request.form.get("title", "").strip()
    if delete_id:
        notices = [n for n in notices if n["id"] != delete_id]
        flash("공지사항을 삭제했습니다.", "success")
    elif not title or len(title) > 80:
        flash("공지 제목을 80자 이내로 입력해 주세요.", "error")
    else:
        notices.append(dict(id=max((n["id"] for n in notices), default=0) + 1, title=title, important=bool(request.form.get("important")), date=datetime.now().strftime("%Y.%m.%d %H:%M")))
        flash("공지사항을 등록했습니다. 참여자 상세 화면에 바로 보여요.", "success")
    product["notices"] = notices
    save_product(product)
    return redirect(url_for("manage", product_id=product_id, tab="notice"))

def spreadsheet_safe(value):
    # 엑셀이 수식으로 실행하지 않도록 수식 기호로 시작하는 값 앞에 '를 붙인다.
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text

@app.route("/manage/<int:product_id>/orders.csv")
def manage_csv(product_id):
    product = owned_product(product_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["주문 번호", "이름", "아이디", "색상", "사이즈", "수량", "금액", "주문일"])
    for o in order_rows("orders.product_id=?", (product_id,)):
        writer.writerow([spreadsheet_safe(v) for v in (order_number(o), o["name"] or "", o["username"], o["color"] or "", o["size"] or "", o["quantity"], int(product["price"]) * o["quantity"], o["created_at"])])
    return Response("﻿" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=orders-{product_id}.csv"})

@app.errorhandler(403)
def forbidden(error):
    return page("error.html", "접근할 수 없습니다", message="이 화면은 해당 계정으로 로그인해야 볼 수 있어요."), 403

@app.errorhandler(404)
def not_found(error):
    return page("error.html", "페이지를 찾을 수 없습니다", message="요청한 페이지나 상품이 없습니다. 메뉴에서 다시 선택해 주세요."), 404

@app.errorhandler(413)
def too_large(error):
    return page("error.html", "파일 크기 확인", message="첨부 파일은 전체 10MB 이내로 선택해 주세요."), 413

if __name__ == "__main__":
    app.run(debug=True)
