"""Open Software Platform Flask practice. Run: python app.py"""
import json
import math
import os
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
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
LABELS = {"name": "상품명", "seller_id": "판매자 ID", "price": "가격 (원)", "address": "주소", "status": "상품 상태", "email": "이메일", "start_date": "공동구매 시작일", "end_date": "공동구매 종료일", "pickup_datetime": "상품 수령 일시", "target_amount": "목표 금액 (원)", "target_count": "목표 개수", "manufacturer": "제작 업체", "description": "상품 상세 설명", "category": "카테고리"}
STATUS_LABELS = {"new": "새 상품", "lnew": "새것에 가까움", "used": "중고"}

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
          email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT NOT NULL, student_id TEXT UNIQUE NOT NULL);
        """)
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
    return dict(user=session.get("user"), cart_count=sum(int(x["quantity"]) for x in session.get("cart", [])), labels=LABELS, status_labels=STATUS_LABELS)

@app.template_filter("won")
def won(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"

def page(template, title, badge, active="", **context):
    return render_template(template, page_title=title, badge=badge, active=active, css_file=template.replace(".html", ".css"), **context)

def product_list_context():
    all_products = records("products")
    items = all_products[:]
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    if query:
        items = [p for p in items if query.casefold() in (p["name"] + " " + p.get("manufacturer", "") + " " + p["seller_id"]).casefold()]
    if category:
        items = [p for p in items if p.get("category") == category]
    sort = request.args.get("sort", "popular")
    if sort == "price":
        items.sort(key=lambda p: int(p["price"]))
    elif sort == "popular":
        items.sort(key=lambda p: p.get("participants", 0), reverse=True)
    pages = max(1, math.ceil(len(items) / 2))
    number = min(max(request.args.get("page", 1, type=int), 1), pages)
    return dict(products=items[(number-1)*2:number*2], product_count=len(items), ranking=sorted(all_products, key=lambda p: p.get("participants", 0), reverse=True)[:3], current_page=number, pages=pages, query=query, category=category, sort=sort)

@app.route("/")
def hello():
    return page("index.html", "상품 목록", "PRODUCT", "list", **product_list_context())

@app.route("/list")
def view_list():
    return page("product_list.html", "상품 목록", "PRODUCT", "list", **product_list_context())

@app.route("/reg_items")
def reg_item():
    return page("product_registration.html", "상품 등록", "REGISTRATION", "registration")

@app.route("/submit_item_post", methods=["POST"])
def reg_item_submit_post():
    data = request.form.to_dict()
    try:
        for key in ("name", "seller_id", "price", "address", "status", "email"):
            if not data.get(key, "").strip():
                raise ValueError(f"{LABELS[key]}을 입력해 주세요.")
        if not data["price"].isdigit() or int(data["price"]) < 0:
            raise ValueError("가격은 0 이상의 정수로 입력해 주세요.")
        if data["status"] not in STATUS_LABELS:
            raise ValueError("상품 상태를 확인해 주세요.")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data["email"]):
            raise ValueError("이메일 형식을 확인해 주세요.")
        for key in ("target_amount", "target_count"):
            if data.get(key) and (not data[key].isdigit() or int(data[key]) < (1 if key == "target_count" else 0)):
                raise ValueError(f"{LABELS[key]}을 확인해 주세요.")
        if data.get("start_date") and data.get("end_date") and data["end_date"] < data["start_date"]:
            raise ValueError("종료일은 시작일 이후로 지정해 주세요.")
        image, filename = image_upload(required=True)
    except ValueError as error:
        return page("error.html", "입력 확인", "NOTICE", "registration", message=str(error)), 400
    item = dict(data, image=image, participants=0)
    with connect() as db:
        product_id = db.execute("INSERT INTO products(data) VALUES(?)", (json.dumps(item, ensure_ascii=False),)).lastrowid
    return page("result.html", "상품 등록 결과", "RESULT", "registration", data=data, original_filename=filename, img_path=url_for("static", filename=image), product_id=product_id)

@app.route("/product_detail")
def product_detail():
    return page("product_detail.html", "상품 상세", "DETAIL", "list", product=product_by_id(request.args.get("id", 1, type=int)))

@app.route("/review")
def view_review():
    reviews = records("reviews")
    product_id = request.args.get("product_id", type=int)
    if product_id:
        reviews = [r for r in reviews if r["product_id"] == product_id]
    if request.args.get("sort") == "rating":
        reviews.sort(key=lambda r: r["rating"], reverse=True)
    products = {p["id"]: p for p in records("products")}
    pages = max(1, math.ceil(len(reviews) / 2))
    number = min(max(request.args.get("page", 1, type=int), 1), pages)
    average = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
    return page("review_list.html", "리뷰 목록", "REVIEW", "review", reviews=reviews[(number-1)*2:number*2], products=products, review_count=len(reviews), average=average, current_page=number, pages=pages, product_id=product_id)

@app.route("/review_detail")
def review_detail():
    review_id = request.args.get("id", 1, type=int)
    review = next((r for r in records("reviews") if r["id"] == review_id), None)
    if not review:
        abort(404)
    return page("review_detail.html", "리뷰 상세", "REVIEW", "review", review=review, product=product_by_id(review["product_id"]))

@app.route("/reg_reviews", methods=["GET", "POST"])
def reg_review():
    products = records("products")
    product_id = request.values.get("product_id", 2, type=int)
    product = product_by_id(product_id)
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
                data = dict(product_id=product_id, title=title, description=description, rating=rating, author=session.get("user", {}).get("username", "User"), date=datetime.now().strftime("%Y.%m.%d"), image=image, size="M", color="블랙")
                with connect() as db:
                    review_id = db.execute("INSERT INTO reviews(data) VALUES(?)", (json.dumps(data, ensure_ascii=False),)).lastrowid
                flash("리뷰가 등록되었습니다.", "success")
                return redirect(url_for("review_detail", id=review_id))
    return page("review_writing.html", "리뷰 작성", "REVIEW", "writing", products=products, product=product)

@app.route("/cart")
def cart():
    entries = []
    for item in session.get("cart", []):
        p = product_by_id(item["product_id"])
        entries.append(dict(item, product=p, subtotal=int(p["price"]) * int(item["quantity"])))
    return page("cart.html", "장바구니", "CART", "cart", entries=entries, total=sum(x["subtotal"] for x in entries))

@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", type=int)
    product_by_id(product_id)
    quantity = max(1, min(request.form.get("quantity", 1, type=int), 99))
    entries = session.get("cart", [])
    options = dict(size=request.form.get("size", "M"), color=request.form.get("color", "그린"))
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
    if request.form.get("product_id", type=int):
        p = product_by_id(request.form.get("product_id", type=int))
        entries = [dict(product_id=p["id"], quantity=max(1, min(request.form.get("quantity", 1, type=int), 99)), size=request.form.get("size", "M"), color=request.form.get("color", "그린"))]
    else:
        entries = session.get("cart", [])
    if not entries:
        flash("참여할 상품을 먼저 담아 주세요.", "error")
        return redirect(url_for("cart"))
    orders = session.get("orders", [])
    for entry in entries:
        p = product_by_id(entry["product_id"])
        orders.append(dict(entry, name=p["name"], date=datetime.now().strftime("%Y.%m.%d")))
        p["participants"] = p.get("participants", 0) + entry["quantity"]
        p.pop("id")
        with connect() as db:
            db.execute("UPDATE products SET data=? WHERE id=?", (json.dumps(p, ensure_ascii=False), entry["product_id"]))
    session["orders"] = orders[-20:]
    if not request.form.get("product_id"):
        session["cart"] = []
    flash("공동구매 참여가 기록되었습니다. 실제 결제는 진행되지 않습니다.", "success")
    return redirect(url_for("account"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        values = {key: request.form.get(key, "").strip() for key in ("username", "email", "password", "password_confirm", "name", "student_id")}
        password = values["password"]
        error = None
        if not all(values.values()):
            error = "모든 필수 항목을 입력해 주세요."
        elif not re.fullmatch(r"[A-Za-z0-9_]{3,30}", values["username"]):
            error = "ID는 영문, 숫자, 밑줄을 사용해 3~30자로 입력해 주세요."
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]):
            error = "이메일 형식을 확인해 주세요."
        elif len(password) < 10 or not all(re.search(pattern, password) for pattern in (r"[A-Z]", r"[a-z]", r"[0-9]")):
            error = "비밀번호는 대문자, 소문자, 숫자를 포함해 10자 이상으로 입력해 주세요."
        elif password != values["password_confirm"]:
            error = "비밀번호 확인이 일치하지 않습니다."
        if error:
            flash(error, "error")
        else:
            try:
                with connect() as db:
                    db.execute("INSERT INTO users(username,email,password_hash,name,student_id) VALUES(?,?,?,?,?)", (values["username"], values["email"], generate_password_hash(password), values["name"], values["student_id"]))
            except sqlite3.IntegrityError:
                flash("이미 등록된 ID, 이메일 또는 학번입니다.", "error")
            else:
                flash("회원가입이 완료되었습니다. 로그인해 주세요.", "success")
                return redirect(url_for("login"))
    return page("signup.html", "회원가입", "SIGNUP", "login")

@app.route("/check_id")
def check_id():
    username = request.args.get("username", "")
    with connect() as db:
        taken = bool(db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone())
    valid = bool(re.fullmatch(r"[A-Za-z0-9_]{3,30}", username))
    return dict(available=valid and not taken, message="사용 가능한 ID입니다." if valid and not taken else "사용할 수 없는 ID입니다.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with connect() as db:
            user = db.execute("SELECT * FROM users WHERE username=?", (request.form.get("username", ""),)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session["user"] = {key: user[key] for key in ("username", "name", "email", "student_id")}
            flash("로그인되었습니다.", "success")
            return redirect(url_for("account"))
        flash("ID 또는 비밀번호를 확인해 주세요.", "error")
    return page("login.html", "로그인/로그아웃", "LOGIN", "login")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("login"))

@app.route("/account")
def account():
    return page("account.html", "마이페이지", "ACCOUNT", "account", orders=session.get("orders", []))

@app.errorhandler(404)
def not_found(error):
    return page("error.html", "페이지를 찾을 수 없습니다", "NOTICE", message="요청한 페이지나 상품이 없습니다. 메뉴에서 다시 선택해 주세요."), 404

@app.errorhandler(413)
def too_large(error):
    return page("error.html", "파일 크기 확인", "NOTICE", message="첨부 파일은 전체 10MB 이내로 선택해 주세요."), 413

if __name__ == "__main__":
    app.run(debug=True)
