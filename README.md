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

## 07.Flask Practice 요구사항

- `/`에서 `index.html`을 렌더링합니다.
- 모든 페이지는 `index.html`을 사용하며 공통 내비게이션을 표시합니다.
- 상품 목록, 상품 등록, 리뷰 목록, 리뷰 등록에 실제 링크가 있습니다.
- 상품 등록 폼에는 상품명, 판매자 ID, 가격, 주소, 상품 상태, 이메일, 사진의 필수 7개 항목이 있습니다.
- `method="post"`, `enctype="multipart/form-data"`로 텍스트와 파일을 함께 전송합니다.
- 서버는 `request.form`과 `request.files`로 입력을 받습니다.
- `result.html`에는 필수 항목뿐 아니라 일정·목표 금액 등 추가로 전송한 모든 텍스트와 사진 파일명·실제 사진이 표시됩니다.
- 사진은 `static/images/uploads/`에 저장됩니다.
- `python app.py`로 실행합니다.
- ZIP에 `venv`, `.git`, 테스트 데이터베이스, 개인 세션 키를 포함하지 않습니다.

## 제출 전 확인

1. 상품 등록 화면에 7개 항목과 사진을 입력합니다. 처음에는 `static/images/practice_sample.png`를 사진으로 선택해도 됩니다.
2. 등록 버튼을 누르기 **전** 입력한 상품 등록 화면을 캡처합니다. 긴 화면은 전체 페이지 캡처를 사용하거나 모든 입력 내용이 확인되도록 촬영하세요.
3. **상품 등록하기**를 눌러 결과 화면에 같은 값과 사진이 표시되는지 확인합니다.
4. 결과 화면을 캡처합니다. 주소가 `/submit_item_post`인 것은 정상입니다.
5. `static/images/uploads/`의 실습 사진도 GitHub에 올립니다. 이 폴더는 `.gitignore`에서 제외하지 않았습니다.
6. 기존 팀 저장소에 커밋·push하고 GitHub URL과 두 화면의 스크린샷을 팀당 한 번 제출합니다.

## 구현된 동작

- 상단 및 사이드바 메뉴와 상품·리뷰 상세 링크
- 상품 검색, 카테고리 필터, 정렬, 실제 데이터 수에 따른 페이지 이동
- 상품 등록 및 목록·상세 반영
- 리뷰 등록 및 목록·상세 반영
- 상품 옵션 선택, 장바구니 추가·삭제, 공동구매 참여 내역 기록
- 로컬 회원가입, ID 중복 확인, 로그인·로그아웃, 비밀번호 보기
- 상품·리뷰 입력 임시 저장 및 불러오기. 사진은 브라우저 보안상 다시 선택해야 합니다.
- 파일 선택 및 드래그 앤 드롭, 사진 미리보기
- 모바일 메뉴와 오류 안내

회원가입과 상품·리뷰 정보는 실행 시 생성되는 로컬 SQLite에 저장합니다. 비밀번호는 해시로 저장합니다. 장바구니·참여 내역은 현재 브라우저 세션에 저장합니다. 실제 결제, 학생 인증, 이메일 계정 복구, 자동 매칭·달성 알림은 외부 서비스와 연동하지 않았습니다. 해당 기능을 실제 처리한 것처럼 표시하지 않으며, 계정 찾기 버튼은 연결 범위를 설명하는 안내창을 엽니다.

## 사진 자리 바꾸기

기존 참고 화면의 사진 영역은 회색 빈 박스로 유지했습니다. 누락된 이미지 파일을 억지로 연결하지 않으므로 깨진 이미지 아이콘이 나타나지 않습니다.

공통 `photo()` 매크로를 사용한 자리에는 사진 경로를 지정할 수 있습니다. 예를 들어 `static/images/my_photo.png`를 넣었다면:

```jinja2
{{ photo('images/my_photo.png', 'light', '상품 사진') }}
```

실제로 등록한 상품·리뷰 사진은 해당 목록·상세 화면에 자동으로 표시됩니다. 수정본에 포함한 폰트는 Noto Sans KR이며, 라이선스는 `static/fonts/LICENSE.txt`에 있습니다.
