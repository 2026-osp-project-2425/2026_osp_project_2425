# 이화인을 위한 간편 공동구매 플랫폼

이화여자대학교 재학생을 위한 Flask 기반 공동구매 마켓입니다. 상품 탐색과 등록, 공동구매 참여, 리뷰 작성·조회, 회원가입·로그인을 하나의 웹사이트에서 제공합니다.

Open Software Platform 실습 프로젝트로, Firebase Realtime Database를 연동해 상품 등록 정보와 회원가입 정보를 저장합니다. 화면에는 작업용 이름인 **EwhaMarket**을 사용하며, 서비스명은 추후 확정 예정입니다.

## 주요 기능

| 구분 | 기능 |
| --- | --- |
| 상품 탐색 | 목록·상세 조회, 검색, 카테고리 필터, 정렬 |
| 상품 등록 | 기본 정보, 사진, 공동구매 일정, 목표 개수, 사이즈·색상 옵션 등록 |
| 공동구매 참여 | 옵션·수량 선택, 장바구니, 참여 내역 확인 |
| 진행자 관리 | 등록 상품 수정, 참여자·주문 확인, 공지 관리, CSV 다운로드 |
| 리뷰 | 목록·상세 조회, 평점·후기·사진 등록 |
| 계정 | 회원가입, ID 중복 확인, 비밀번호 해시 저장, 로그인·로그아웃, 회원정보 수정 |
| 화면 편의 | 사진 미리보기, 드래그 앤 드롭, 상품 입력 임시 저장, 반응형 레이아웃 |

실제 결제와 학생증을 통한 재학생 인증은 구현하지 않은 실습용 서비스입니다.

## 개발 환경

| 항목 | 구성 |
| --- | --- |
| 실행 환경 | Python 3.9 이상 |
| 웹 서버 | Flask 3.1 이상, 4 미만 |
| 화면 | Jinja2, HTML, CSS, JavaScript |
| 로컬 데이터 | SQLite |
| 클라우드 데이터 | Firebase Realtime Database |
| Firebase 연동 | Firebase Admin Python SDK 7 이상, 8 미만 |
| 비밀번호·로그인 상태 | Werkzeug 해시 생성·검증, Flask 세션 |

필요한 Python 라이브러리는 `requirements.txt`로 설치합니다.

## 실행 방법

모든 명령은 **`app.py`가 있는 프로젝트 폴더**에서 실행합니다. 수정 완료된 저장소를 새로 clone한 경우에도 아래 순서대로 준비합니다.

### 1. Firebase 설정

1. [Firebase 콘솔](https://console.firebase.google.com/)에서 프로젝트를 생성하고 웹 앱을 등록합니다.
2. **Realtime Database**를 생성합니다. Python Admin SDK로 접근하므로 잠금 모드로 시작할 수 있습니다.
3. 프로젝트 설정의 **서비스 계정 → 새 비공개 키 생성**에서 JSON 인증키를 받습니다.
4. `app.py`와 같은 위치에 `authentication` 폴더를 만들고, 인증키를 `firebase-key.json`으로 저장합니다.
5. `database.py`의 `DATABASE_URL`이 사용할 데이터베이스 주소와 일치하는지 확인합니다.

인증키의 프로젝트 기준 경로는 `authentication/firebase-key.json`입니다. **인증키는 GitHub에 올리지 않습니다.**

현재 코드의 기본 연결 대상은 `ewhamarket-2425` 프로젝트의 싱가포르 Realtime Database입니다. 다른 프로젝트를 사용할 경우 해당 프로젝트의 인증키와 데이터베이스 URL을 함께 설정합니다.

### 2. 가상환경과 라이브러리 설치

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

PowerShell에서 가상환경 활성화가 제한되면 가상환경의 Python을 직접 사용합니다.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Firebase 연결 확인

```powershell
python database.py
```

정상 연결 시 다음과 같이 표시됩니다.

```text
Firebase 연결 성공!
DB가 비어 있습니다. 정상입니다.
```

이미 데이터가 있으면 두 번째 줄은 `기존 데이터가 있습니다.`로 표시됩니다. 이 명령은 데이터 읽기로 연결을 확인하며 새 데이터를 저장하지 않습니다.

### 4. 웹 서버 실행

```powershell
python app.py
```

가상환경을 활성화하지 않은 Windows 환경에서는 다음을 사용합니다.

```powershell
.\venv\Scripts\python.exe app.py
```

브라우저에서 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)에 접속합니다.

- 사이트를 사용하는 동안 서버 터미널을 열어둡니다. 종료는 `Ctrl+C`입니다.
- HTML 파일을 직접 열거나 Live Server로 실행하지 않고 Flask 서버 주소에 접속합니다.
- Chrome 확대 비율은 `Ctrl+0`으로 100%에 맞춥니다.
- 수정한 CSS가 반영되지 않으면 `Ctrl+Shift+R`로 새로고침합니다.

처음 준비를 마친 뒤에는 가상환경에서 **`python app.py`만 실행**하면 됩니다. `python database.py`는 연결을 별도로 확인할 때 사용합니다.


## 데이터 저장 방식

| 저장 위치 | 역할 |
| --- | --- |
| `instance/market.sqlite3` | 상품·회원·주문·리뷰 등 기존 서비스 데이터 |
| Firebase `item/{상품명}` | 상품 입력값, 이미지 경로, 공동구매 추가 정보 |
| Firebase `user/{ID}` | 회원가입 정보와 비밀번호 해시 |
| `static/images/uploads/` | 업로드한 상품·리뷰 사진 파일 |
| `instance/session.key` | 로컬 실행 시 사용하는 세션 서명 키 |

사진 파일은 기존 로컬 폴더에 저장하고 Firebase에는 `img_path`로 경로를 저장합니다.

**다른 컴퓨터에서 clone해도 Firebase 데이터만으로 기존 로컬 계정·상품·주문이 자동 복원되지는 않습니다.** Firebase 연결 전에 생성한 SQLite 데이터도 자동으로 전체 이전하지 않습니다.

**비밀번호 원문과 비밀번호 확인 값은 저장하지 않습니다.** ID는 영문·숫자·밑줄을 사용한 3~30자, 닉네임은 30자 이하입니다. 비밀번호는 대문자·소문자·숫자를 포함한 10자 이상으로 입력합니다.

학생증 사진은 실제 인증·서버 저장 기능이 없는 기존 실습용 미리보기입니다. 화면에서 이미지 선택을 요구하면 실제 학생증 대신 테스트 이미지를 사용합니다.

## 파일 구성

| 위치 | 역할 |
| --- | --- |
| `app.py` | 페이지 라우팅, POST 처리, 사진 저장, 상품·리뷰·계정·주문 처리 |
| `database.py` | Firebase 연결, 상품·회원 저장, 중복 검사 및 정보 갱신 |
| `requirements.txt`, `.gitignore` | 라이브러리 목록, Git 제외 설정 |
| `templates/index.html` | 메인 화면, 공통 사이드바·헤더·내비게이션, 템플릿 매크로 |
| `templates/product_registration.html` | 상품 등록·수정 폼 |
| `templates/result.html` | 등록한 상품 정보와 사진을 표시하는 결과 화면 |
| `templates/product_list.html`, `templates/product_detail.html` | 상품 목록·상세 |
| `templates/review_list.html`, `templates/review_detail.html`, `templates/review_writing.html` | 리뷰 목록·상세·등록 |
| `templates/signup.html`, `templates/login.html` | 회원가입·로그인 |
| `templates/cart.html` | 장바구니 |
| `templates/account.html`, `templates/account_edit.html` | 계정·참여 내역, 회원정보 수정 |
| `templates/manage.html` | 진행자의 공동구매 관리 |
| `templates/joined_detail.html`, `templates/order_done.html` | 참여 상세·완료 화면 |
| `templates/error.html` | 입력 오류 및 없는 페이지 안내 |
| `static/css/common.css` | 공통 색상·요소·반응형 레이아웃 |
| `static/css/페이지명.css` | 페이지별 스타일 |
| `static/css/fonts.css` | 로컬 폰트 선언. 사용 시 참조하는 폰트 파일도 별도 준비 |
| `static/main.js` | 사진 미리보기, 드래그 앤 드롭, 임시 저장, ID 확인 등 |
| `static/images/uploads/` | 상품·리뷰 사진 저장 위치. Git 제외 |
| `authentication/firebase-key.json` | 로컬 Firebase 인증키. Git 제외 |
| `instance/` | SQLite 데이터, 세션 키, 수정본 적용 백업. Git 제외 |

테스트용 업로드 사진은 별도로 준비합니다. 폰트나 샘플 이미지 파일을 추가로 사용할 경우 해당 파일이 실제 프로젝트에 포함되어 있는지 확인합니다.

## 주요 페이지와 요청 주소

| 주소 | 메서드 | 역할 |
| --- | --- | --- |
| `/` | GET | 메인 화면 |
| `/list` | GET | 상품 목록 |
| `/reg_items` | GET | 상품 등록 화면 |
| `/submit_item_post` | POST | 상품 등록, Firebase 저장, 결과 화면 표시 |
| `/product_detail?id=1` | GET | 상품 상세 |
| `/products/<product_id>/edit` | GET / POST | 등록 상품 수정 |
| `/review` | GET | 리뷰 목록 |
| `/reg_reviews` | GET / POST | 리뷰 등록 |
| `/review_detail?id=1` | GET | 리뷰 상세 |
| `/signup` | GET / POST | 회원가입 |
| `/check_id?username=example` | GET | ID 중복 확인 |
| `/login` | GET / POST | 로그인 |
| `/logout` | POST | 로그아웃 |
| `/cart` | GET | 장바구니 |
| `/participate` | POST | 공동구매 참여 |
| `/account` | GET | 마이페이지·진행·참여 내역 |
| `/account/edit` | GET / POST | 회원정보 수정 |
| `/joined/<order_id>` | GET | 참여 상세 |
| `/order_done/<order_id>` | GET | 참여 완료 |
| `/manage/<product_id>` | GET | 진행자의 공동구매 관리 |

상품·주문 ID는 실제 저장된 값으로 바꿔 접근합니다. 본인 소유 상품이나 주문만 접근할 수 있는 화면은 로그인과 권한 확인이 필요합니다.

## 인증키와 Git 관리

`.gitignore`에 다음 항목을 유지합니다.

```gitignore
authentication/
venv/
.venv/
instance/
.env
__pycache__/
static/images/uploads/
apply_firebase.py
firebase_patch/
```

### 제외 설정과 추적 해제

아래 명령도 `firebase_patch` 폴더가 아닌 **clone한 Git 저장소 폴더**에서 실행합니다.

```powershell
git rev-parse --show-toplevel
git check-ignore -v authentication/firebase-key.json
```

첫 명령은 저장소 위치를 보여줍니다. 두 번째 명령에서 `.gitignore`의 `authentication/` 규칙과 파일 경로가 표시되면 제외 규칙이 적용된 것입니다. 이미 추적 중인 파일은 먼저 추적 해제가 필요합니다.

`.gitignore`는 이미 추적 중인 파일을 자동으로 제외하지 않습니다. 아래 명령은 **컴퓨터의 파일은 유지하고 Git 추적만 해제**합니다.

```powershell
git rm -r --cached --ignore-unmatch authentication venv .venv instance
```

로컬 인증키가 남아 있는지는 다음으로 확인합니다. `True`는 컴퓨터에 파일이 존재한다는 뜻입니다.

```powershell
Test-Path .\authentication\firebase-key.json
```

`git status --short`에 다음처럼 표시되면 인증키를 **저장소에서 제거하는 변경이 스테이징된 상태**입니다.

```text
D  authentication/firebase-key.json
```

인증키 내용을 새로 업로드하는 표시가 아닙니다. 삭제 변경을 커밋하면 이후 커밋의 파일 목록에서 제거됩니다. **이전 커밋에 포함됐던 내용은 이 작업만으로 과거 기록에서 없어지지 않습니다.**

인증키를 이미 GitHub에 push한 적이 있다면 기존 서비스 계정 키를 폐기하고 새 키를 발급해 로컬 파일을 교체합니다.
