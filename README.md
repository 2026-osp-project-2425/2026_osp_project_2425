# 이화인을 위한 간편 공동구매 플랫폼

이화여자대학교 재학생을 위한 공동구매 마켓의 Flask 실습 프로젝트입니다. 상품 탐색, 상품 등록, 리뷰 작성과 조회를 하나의 웹사이트에서 진행할 수 있도록 구성했습니다. 서비스명은 추후 확정 예정입니다.

## 실행 방법

Python 3.9 이상이 필요합니다. 아래 명령은 `app.py`가 있는 프로젝트 폴더에서 실행합니다.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

PowerShell에서 가상환경 활성화가 제한되는 경우:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

macOS/Linux에서는 `source venv/bin/activate`로 활성화합니다.

브라우저에서 **http://127.0.0.1:5000/** 에 접속합니다. Chrome 확대/축소는 **100%**로 두세요. HTML 더블클릭 또는 Live Server 대신 Flask 서버 주소로 접속해야 템플릿과 POST 전송이 동작합니다.

## 기존 프로젝트에 적용

1. 기존 서버를 실행 중이면 터미널에서 `Ctrl+C`로 종료합니다.
2. 기존 파일을 별도로 백업합니다.
3. ZIP을 풀고 `app.py`, `requirements.txt`, `.gitignore`, `templates/`, `static/`을 적용합니다. 원래 저장소의 `.git/`는 유지합니다.
4. 새 파일명을 사용하는 수정본입니다. 기존 공백이 포함된 HTML/CSS나 `Review Writinghtml` 같은 이전 파일은 이 수정본에서 참조하지 않습니다. 새 `templates/`와 `static/` 코드로 통일하세요.
5. 의존성을 설치하고 `python app.py`로 서버를 다시 실행합니다.
6. Chrome에서 `Ctrl+0`으로 100%로 맞추고 `Ctrl+Shift+R`로 이전 CSS 캐시를 갱신합니다.

## 파일 구성

| 위치 | 역할 |
| --- | --- |
| `app.py` | 페이지 라우팅, POST 요청, 사진 저장, 상품·리뷰·계정 처리 |
| `templates/index.html` | 메인 화면과 모든 페이지의 공통 사이드바·헤더·내비게이션 및 템플릿 매크로 |
| `templates/product_registration.html` | 상품 등록 폼 |
| `templates/result.html` | 입력한 모든 상품 정보와 사진을 표시하는 결과 화면 |
| `templates/product_list.html`, `product_detail.html` | 상품 목록·상세 |
| `templates/review_list.html`, `review_detail.html`, `review_writing.html` | 리뷰 목록·상세·등록 |
| `templates/signup.html`, `login.html` | 회원가입·로그인 |
| `templates/cart.html`, `account.html` | 장바구니·계정 및 참여 내역 |
| `templates/error.html` | 입력 오류 및 없는 페이지 안내 |
| `static/css/common.css` | 모든 화면의 색상, 공통 요소, 반응형 레이아웃 |
| `static/css/페이지명.css` | 페이지별 스타일 |
| `static/css/fonts.css`, `static/fonts/` | 로컬 한글 폰트와 라이선스 |
| `static/main.js` | 사진 미리보기, 드래그 앤 드롭, 임시 저장, ID 확인 등 |
| `static/images/practice_sample.png` | 과제 사진 업로드 확인에 사용할 수 있는 샘플 이미지 |
| `static/images/uploads/` | 등록한 상품·리뷰 사진이 저장되는 위치 |
| `instance/` | 실행 시 생성되는 SQLite 데이터와 세션 키. Git에서 제외 |

## 페이지 주소

| 주소 | 화면 |
| --- | --- |
| `/` | `index.html` 메인 화면 |
| `/list` | 상품 목록 |
| `/reg_items` | 상품 등록 |
| `/submit_item_post` | 상품 정보를 POST로 받고 `result.html`을 표시 |
| `/product_detail?id=1` | 상품 상세 |
| `/review` | 리뷰 목록 |
| `/reg_reviews` | 리뷰 등록 |
| `/review_detail?id=1` | 리뷰 상세 |
| `/signup` | 회원가입 |
| `/login` | 로그인 |
| `/cart` | 장바구니 |
| `/account` | 계정·공동구매 참여 내역 |

