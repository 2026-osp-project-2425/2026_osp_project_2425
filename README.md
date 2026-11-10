# 이화 공동구매 · EwhaMarket

이화여자대학교 구성원을 위한 Flask 기반 공동구매 실습 프로젝트입니다. 상품을 등록하고 찾아보는 기능부터 공동구매 참여, 진행 상품 관리, 후기 작성까지 하나의 웹사이트에서 제공합니다.

상품·회원·사진은 Firebase Realtime Database에 저장합니다. 팀원들이 같은 데이터베이스에 연결하면 다른 컴퓨터에서 등록한 상품과 계정을 사용할 수 있으며, 새로고침하거나 다음 화면을 조회할 때 변경 사항이 반영됩니다.

## 주요 기능

| 구분 | 기능 |
| --- | --- |
| 계정 | 회원가입, ID 중복 확인, 로그인·로그아웃, 회원정보 수정 |
| 상품 탐색 | 상품 목록·상세 조회, 검색, 카테고리·진행 상태 필터, 정렬 |
| 페이지 나누기 | 한 페이지에 상품 4개 표시, 페이지 번호로 이동 |
| 상품 등록 | 상품 정보, 대표 사진, 공동구매 일정, 수령 장소, 목표 개수, 옵션 등록 |
| 상품 관리 | 판매자의 상품 수정, 참여자 확인, 공지 관리, 주문 내역 CSV 내보내기 |
| 공동구매 참여 | 옵션·수량 선택, 장바구니, 참여 내역 확인 |
| 리뷰 | 후기·평점·사진 작성, 리뷰 목록·상세 조회 |
| 화면 편의 | 사진 미리보기, 입력 임시 저장, 비밀번호 표시 전환, 반응형 화면 |

실제 결제와 학생증을 통한 재학생 인증은 연결하지 않은 실습용 서비스입니다. 상품·회원·사진은 여러 컴퓨터에서 공유하지만, 주문·리뷰 내역은 현재 실행 중인 컴퓨터의 SQLite에 저장합니다.

## 개발 환경

| 항목 | 사용 기술 |
| --- | --- |
| 언어 | Python, JavaScript |
| 웹 서버 | Flask 3.1 이상, 4 미만 |
| 화면 | Jinja2, HTML, CSS |
| 공용 데이터 | Firebase Realtime Database |
| Firebase 연동 | Firebase Admin Python SDK 7 이상, 8 미만 |
| 로컬 데이터 | SQLite |
| 비밀번호·로그인 상태 | Werkzeug 비밀번호 해시, Flask 세션 |

Python 3.10 이상을 권장합니다. 필요한 Python 패키지는 `requirements.txt`에 정리되어 있습니다.

## 프로젝트 구성

| 파일·폴더 | 역할 |
| --- | --- |
| `app.py` | Flask 실행, 페이지 라우팅, 폼 처리, 로그인·상품·참여·리뷰 처리 |
| `database.py` | Firebase 연결, 상품·회원·공유 사진 저장과 조회 |
| `requirements.txt` | Python 패키지 목록 |
| `README.md` | 프로젝트 소개와 실행 안내 |
| `.gitignore` | 인증키·가상환경·로컬 데이터 등의 Git 제외 설정 |
| `templates/` | 페이지별 HTML과 공통 Jinja2 템플릿 |
| `templates/index.html` | 공통 메뉴·헤더, 상품 카드, 페이지 번호 등 |
| `static/css/` | 공통 스타일과 페이지별 스타일 |
| `static/main.js` | 사진 미리보기, 입력 처리, 화면 조작 |
| `static/images/uploads/` | 이전 버전에서 저장한 로컬 사진. 기존 화면이 참조할 수 있음 |
| `authentication/firebase-key.json` | 로컬 실행용 Firebase 서비스 계정 인증키. Git 제외 |
| `instance/market.sqlite3` | 로컬 주문·리뷰와 이전 데이터의 호환 정보. Git 제외 |
| `instance/session.key` | 세션 서명 키. 최초 실행 시 없으면 생성 |

인증키와 `instance/`는 각 실행 환경에서 준비하거나 생성하는 파일이며, 저장소에 함께 올리지 않습니다.

## 실행 방법

모든 명령은 **`app.py`가 있는 프로젝트 폴더**에서 실행합니다.

### 1. Firebase 설정

1. 팀이 사용하는 Firebase 프로젝트의 Realtime Database를 준비합니다.
2. 해당 DB에 접근할 권한이 있는 서비스 계정 JSON 키를 준비합니다.
3. 프로젝트 안에 `authentication` 폴더를 만들고 키를 `firebase-key.json`으로 저장합니다.
4. `database.py`의 `DATABASE_URL`이 사용할 Realtime Database 주소인지 확인합니다.

모든 팀원이 같은 데이터베이스 주소를 사용해야 합니다. 키 파일 자체가 같을 필요는 없지만, 각 키가 해당 DB에 접근할 권한을 가지고 있어야 합니다.

필요하면 `OSP_DATABASE_URL`, `OSP_FIREBASE_KEY` 환경변수로 DB 주소와 인증키 경로를 지정할 수 있습니다. 별도 설정이 없다면 코드의 기본 DB 주소와 `authentication/firebase-key.json`을 사용합니다.

**비공개 키는 GitHub에 올리지 않습니다.**

### 2. 가상환경과 패키지 설치

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

PowerShell에서 가상환경 활성화가 제한되면 가상환경의 Python을 직접 사용합니다.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Firebase 연결 확인

```powershell
python database.py
```

`Firebase 연결 성공!`이 출력되면 연결된 상태입니다. 이 명령은 연결을 확인하며 새 상품을 등록하지 않습니다.

가상환경을 활성화하지 않은 Windows 환경에서는 다음을 실행합니다.

```powershell
.\venv\Scripts\python.exe database.py
```

### 4. 웹 서버 실행

```powershell
python app.py
```

가상환경을 활성화하지 않은 Windows 환경:

```powershell
.\venv\Scripts\python.exe app.py
```

브라우저에서 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)에 접속합니다.

- HTML 파일을 직접 열거나 Live Server로 실행하지 않고 Flask 주소로 접속합니다.
- 사이트를 사용하는 동안 서버 터미널을 열어 둡니다. 종료는 `Ctrl+C`입니다.
- 최초 준비 후에는 가상환경을 활성화하고 `python app.py`로 실행하면 됩니다.

## 데이터 저장과 공유

| 저장 위치 | 내용 | 컴퓨터 간 공유 |
| --- | --- | --- |
| Firebase `item/{상품ID}` | 상품 정보, 판매자 ID, 가격, 일정, 옵션, 이미지 참조 | 공유 |
| Firebase `user/{사용자ID}` | 회원정보와 비밀번호 해시 | 공유 |
| Firebase `product_images/{이미지ID}` | 사진의 Base64 데이터와 MIME 타입 | 공유 |
| SQLite `orders` | 공동구매 참여·주문 내역 | 로컬 |
| SQLite `reviews` | 후기·평점 등 리뷰 데이터 | 로컬 |
| Flask 세션 | 로그인 상태와 장바구니 | 해당 브라우저 |

### 상품 ID

새 상품은 Firebase의 `push()`로 고유 ID를 발급받습니다. 상품 이름을 변경해도 해당 ID는 유지됩니다. 같은 이름의 상품을 여러 개 등록할 수 있으며 ID로 구분합니다.

이전 버전의 `item/상품명` 데이터는 기존 Firebase 키를 공통 ID로 사용합니다. 예전 `local_id`는 컴퓨터마다 중복될 수 있으므로 공통 상품 ID로 사용하지 않습니다.

### 사진

새 사진은 Realtime Database의 별도 노드에 저장하고 `/media/{이미지ID}`로 제공합니다. 별도의 Firebase Storage 버킷은 사용하지 않습니다. 지원 형식은 PNG, JPG, JPEG, GIF, WEBP이며 파일당 최대 5MB입니다. 현재 신규 등록 처리는 대표 사진 1장을 저장합니다.

이전 로컬 사진은 공유 저장소로 옮기기 전까지 해당 컴퓨터의 파일이 필요합니다. 기존 업로드 폴더를 통째로 지우면 예전 상품·리뷰 사진이 표시되지 않을 수 있습니다.

### 계정과 로그인

회원가입한 계정과 비밀번호 해시는 Firebase에 저장합니다. 비밀번호 원문이나 확인 값은 저장하지 않습니다. 로그인 성공 시 세션에 사용자 정보와 `id`를 저장합니다. 실패 시 중앙 팝업을 표시하고 로그인 화면을 유지하며, 로그아웃하면 세션 전체를 삭제하고 메인으로 이동합니다.

Firebase에 없는 이전 로컬 전용 계정은 비밀번호를 올바르게 입력한 경우 Firebase로 이전될 수 있습니다. 현재 회원 중복 검사는 사용자 ID를 기준으로 하며 이메일·학번의 전역 유일성은 보장하지 않습니다.

## 주요 페이지

| 주소 | 메서드 | 설명 |
| --- | --- | --- |
| `/` | GET | 메인 상품 목록 |
| `/list` | GET | 상품 목록·검색·필터·정렬 |
| `/list?page=2` | GET | 상품 목록 2페이지 |
| `/reg_items` | GET | 상품 등록 화면 |
| `/submit_item_post` | POST | 상품과 사진 등록 |
| `/products/{상품ID}` | GET | 상품 상세 |
| `/products/{상품ID}/edit` | GET / POST | 판매자의 상품 수정 |
| `/media/{이미지ID}` | GET | 공유 사진 조회 |
| `/signup` | GET / POST | 회원가입 |
| `/check_id` | GET | ID 중복 확인 |
| `/login` | GET / POST | 로그인 |
| `/logout` | POST | 로그아웃 |
| `/account` | GET | 마이페이지 |
| `/account/edit` | GET / POST | 회원정보 수정 |
| `/cart` | GET | 장바구니 |
| `/participate` | POST | 공동구매 참여 |
| `/review` | GET | 리뷰 목록 |
| `/reg_reviews` | GET / POST | 리뷰 작성 |
| `/review_detail?id={리뷰ID}` | GET | 리뷰 상세 |
| `/manage/{상품ID}` | GET | 판매자의 진행 상품 관리 |

상품을 등록하려면 로그인해야 합니다. 상품 수정·관리 화면은 해당 판매자 계정으로 접근합니다.

## 동작 확인

1. 회원가입 후 로그인하여 사용자 ID와 로그아웃 메뉴를 확인합니다.
2. 잘못된 ID 또는 비밀번호를 입력하여 중앙 팝업을 확인합니다.
3. 사진을 포함한 상품을 등록하고 Firebase `item`에 저장되었는지 확인합니다.
4. 다른 컴퓨터에서 같은 DB에 연결한 뒤 목록·상세·사진을 확인합니다.
5. 한 탭에 상품 5개 이상을 준비하여 목록 1·2페이지가 서로 다른 상품을 표시하는지 확인합니다.
6. 상품 이미지를 눌러 `/products/{상품ID}`로 이동하는지 확인합니다.
7. 로그아웃 후 메인 이동과 로그인 상태 해제를 확인합니다.

페이지당 4개씩 표시하므로 진행 중·마감 탭 각각의 상품 수에 따라 페이지 수가 정해집니다. 두 탭에 상품이 나뉘어 있으면 전체 상품이 5개 이상이어도 각 탭은 1페이지일 수 있습니다.

## Git 관리

인증키, 가상환경, Python 캐시, 로컬 DB·세션 키는 Git에서 제외합니다. 현재 `.gitignore`의 대표 항목은 다음과 같습니다.

```gitignore
authentication/
venv/
.venv/
__pycache__/
instance/
static/images/uploads/
.env
```

이미 Git에 올라간 파일은 `.gitignore`만 추가해도 추적이 해제되지 않습니다. 백업 후 아래 명령으로 인증키·가상환경·로컬 데이터의 **Git 추적만** 해제할 수 있습니다. `--cached`는 실제 로컬 파일을 삭제하지 않습니다.

```powershell
git rm -r --cached --ignore-unmatch authentication venv .venv instance
git status
```

상품·회원·공유 사진은 Firebase에 저장되므로 Git에 데이터 파일을 올릴 필요가 없습니다. 로컬 DB의 변경 사항 취소는 주문·리뷰 등 커밋 전 데이터를 잃게 할 수 있으므로 주의합니다.
