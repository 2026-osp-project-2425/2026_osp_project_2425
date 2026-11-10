# EwhaMarket · 이화 공동구매

이화여자대학교 구성원을 위한 Flask 기반 공동구매 실습 프로젝트입니다. 상품을 등록하고 찾아보며, 공동구매 참여와 후기 작성까지 진행할 수 있습니다.

## 주요 기능

- 회원가입, ID 중복 확인, 로그인·로그아웃, 회원정보 수정
- 상품 등록·수정, 목록·상세 조회, 검색·필터·정렬
- 페이지당 상품 4개 표시 및 페이지 이동
- 상품 사진 공유, 옵션 선택, 장바구니, 공동구매 참여
- 판매자의 진행 상품·참여자·공지 관리, 주문 CSV 내보내기
- 리뷰·평점·사진 작성 및 조회

## 사용 기술

Python, Flask, Jinja2, HTML, CSS, JavaScript, Firebase Realtime Database, SQLite

Python 3.10 이상을 권장하며, 필요한 패키지는 `requirements.txt`에 정리되어 있습니다.

## 실행 방법

1. 팀의 Firebase DB에 접근할 수 있는 서비스 계정 키를 `authentication/firebase-key.json`에 넣습니다.
2. `database.py`의 `DATABASE_URL`을 확인합니다. 모든 팀원이 같은 DB 주소를 사용해야 합니다.
3. `app.py`가 있는 폴더에서 아래 명령을 실행합니다.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python database.py
python app.py
```

브라우저에서 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)에 접속합니다. HTML 파일을 직접 열지 않고 Flask 서버 주소로 접속합니다.

최초 설정 후에는 가상환경을 활성화하고 `python app.py`로 실행하면 됩니다. 서버 종료는 `Ctrl+C`입니다.

## 데이터 저장

| 저장 위치 | 내용 |
| --- | --- |
| Firebase `item/{상품명}` | 상품 정보, 고유 `product_id`, 이미지 경로 |
| Firebase `user/{사용자ID}` | 회원정보와 비밀번호 해시 |
| Firebase `product_images/{이미지ID}` | 공유 사진 데이터 |
| SQLite `instance/market.sqlite3` | 로컬 주문·리뷰 및 이전 데이터의 호환 정보 |

상품·회원·사진은 같은 Firebase에 연결한 컴퓨터에서 공유합니다. 주문·리뷰 내역은 각 컴퓨터의 SQLite에 저장합니다. 로그인 상태와 장바구니는 해당 브라우저의 세션에서 관리합니다.

상품은 상품명을 키로 저장하고, 상세 주소에는 별도 고유 ID를 사용합니다. 같은 상품명의 중복 등록은 차단하며, 이름을 변경해도 고유 ID는 유지합니다.

## 주요 파일

| 파일·폴더 | 역할 |
| --- | --- |
| `app.py` | Flask 실행, 페이지 라우팅, 요청 처리 |
| `database.py` | Firebase 연결 및 데이터 저장·조회 |
| `templates/` | 페이지별 HTML과 공통 템플릿 |
| `static/css/` | 공통·페이지별 스타일 |
| `static/main.js` | 입력 처리, 사진 미리보기 등 화면 동작 |
| `requirements.txt` | Python 패키지 목록 |
| `.gitignore` | 인증키·가상환경·로컬 데이터 등의 Git 제외 설정 |

## 참고 사항

- 사진은 PNG, JPG, JPEG, GIF, WEBP 형식을 지원하며 파일당 최대 5MB입니다.
- 로그인 실패 시 중앙 팝업을 표시하고, 로그아웃하면 세션을 삭제한 뒤 메인으로 이동합니다.
- 목록 2페이지를 확인하려면 진행 중 또는 마감 한 탭에 상품이 최소 5개 필요합니다.
- 실제 결제와 학생증을 통한 재학생 인증은 연결하지 않은 실습용 서비스입니다.
- 인증키, `venv/`, `instance/`는 GitHub에 올리지 않습니다. 기존 DB·사진 파일은 사용 여부를 확인한 뒤 정리합니다.
