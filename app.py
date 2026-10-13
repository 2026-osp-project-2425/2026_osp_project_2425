from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, url_for, abort

app = Flask(__name__)

UPLOAD_FOLDER = Path(app.root_path) / "static" / "images"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

LABELS = {
    "name": "상품명",
    "seller_id": "판매자 ID",
    "price": "가격 (원)",
    "address": "주소",
    "status": "상품 상태",
    "email": "이메일",
    "start_date": "공동구매 시작일",
    "end_date": "공동구매 종료일",
    "pickup_datetime": "상품 수령 일시",
    "target_amount": "목표 금액 (원)",
    "target_count": "목표 개수",
    "manufacturer": "제작 업체",
    "description": "상품 상세 설명",
}

STATUS_LABELS = {
    "new": "새 상품",
    "lnew": "새것에 가까움",
    "used": "중고",
}


@app.route("/")
def hello():
    return render_template(
        "index.html",
        css_file="Product Registration.css"
    )


@app.route("/list")
def view_list():
    return render_template(
        "Product List.html",
        css_file="Product List.css"
    )


@app.route("/reg_items")
def reg_item():
    return render_template(
        "Product Registration.html",
        css_file="Product Registration.css"
    )


@app.route("/review")
def view_review():
    return render_template(
        "Review List.html",
        css_file="Review List.css"
    )


@app.route("/reg_reviews")
def reg_review():
    return render_template(
        "reg_reviews.html",
        css_file="Product Registration.css"
    )


@app.route("/product_detail")
def product_detail():
    return render_template(
        "Product Detail.html",
        css_file="Product Detail.css"
    )


@app.route("/review_detail")
def review_detail():
    return render_template(
        "Review Detail.html",
        css_file="Review Detail.css"
    )


@app.route("/login")
def login():
    return render_template(
        "Login.html",
        css_file="Login.css"
    )


@app.route("/submit_item_post", methods=["POST"])
def reg_item_submit_post():
    data = request.form.to_dict()

    required_fields = [
        "name", "seller_id", "price",
        "address", "status", "email"
    ]

    for field in required_fields:
        if not data.get(field, "").strip():
            abort(400, description=f"{LABELS[field]}을 입력해 주세요.")

    image_file = request.files.get("file_input")

    if image_file is None or image_file.filename == "":
        abort(400, description="상품 사진을 선택해 주세요.")

    extension = Path(image_file.filename).suffix.lower()

    if extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        abort(400, description="사진 파일 형식을 확인해 주세요.")

    # 저장용 이름을 새로 만들어 같은 이름의 사진이 덮어써지지 않게 함
    stored_filename = uuid4().hex + extension
    image_file.save(UPLOAD_FOLDER / stored_filename)

    img_path = url_for(
        "static",
        filename=f"images/{stored_filename}"
    )

    return render_template(
        "result.html",
        css_file="Product Registration.css",
        data=data,
        labels=LABELS,
        status_labels=STATUS_LABELS,
        img_path=img_path,
        original_filename=image_file.filename
    )


if __name__ == "__main__":
    app.run(debug=True)