# EwhaMarket API 명세서

Flask가 HTML 페이지와 API를 같은 서버에서 제공합니다. 경로의 `product_id`는 Firebase 상품명 키와 별개인 상품 고유 ID입니다. 인증은 로그인 후 발급되는 Flask 세션 쿠키를 사용합니다.

## 응답과 요청 형식

- 페이지와 일반 폼은 HTML 또는 `302` 리다이렉트를 반환합니다. 일부 폼 검증 실패는 메시지가 포함된 HTML 또는 리다이렉트로 응답합니다.
- 일반 폼은 `application/x-www-form-urlencoded`로 제출합니다. 사진이 있는 상품·리뷰 폼은 `multipart/form-data`를 사용합니다. 이미지 하나는 최대 5 MiB, 요청 전체는 최대 10 MiB입니다.
- JSON API 요청에는 `Content-Type: application/json`을 지정합니다. 같은 서버의 세션 쿠키를 보냅니다.
- 페이지에서 대상이 없으면 `404`, 소유자 등 필요한 권한이 없으면 `403`, 공유 저장소 오류는 `503`을 반환할 수 있습니다.

## 계정과 로그인

| 메서드 | 경로 | 입력 | 성공 응답 |
| --- | --- | --- | --- |
| GET | `/signup` | — | 회원가입 폼 |
| POST | `/signup` | `username`, `email`, `nickname`, `name`, `password`, `password_confirm`, 선택 `student_id`, `phone` | 로그인으로 이동 |
| GET | `/check_id` | 쿼리 `username` | JSON `{"available":true,"message":"사용 가능한 아이디입니다."}`. 실패 시 `available:false`, 저장소 장애 시 `503` |
| GET | `/login` | 선택 쿼리 `next` | 로그인 폼 |
| POST | `/login` | `username`, `password`, 선택 `next` | 세션 쿠키 발급 후 내부 경로 또는 마이페이지로 이동 |
| POST | `/logout` | — | 세션 종료 후 메인으로 이동 |
| GET | `/account` | 쿼리 `tab=joined\|hosted`, `status=all\|open\|closed` | 본인 마이페이지 또는 비로그인 안내 |
| GET / POST | `/account/edit` | POST `name`, `nickname`, `email`, 선택 `student_id`, `phone` | 본인 정보 수정 폼 또는 마이페이지로 이동 |

## 상품과 공동구매

| 메서드 | 경로 | 입력 | 인증과 응답 |
| --- | --- | --- | --- |
| GET | `/`, `/list` | 쿼리 `q`, `category`, `status=open\|closed`, `sort=popular\|latest\|reviews\|rating`, `page` | 공개 목록. 페이지당 4개, 랭킹은 진행 중 상품의 참여 수 상위 3개 |
| GET | `/products/<id>` | 쿼리 `tab=info\|qna` | 공개 상세 |
| GET | `/reg_items` | — | 로그인 시 등록 폼, 비로그인 시 안내와 로그인으로 이동 |
| GET | `/registration` | 선택 쿼리 `kind=review`, `product_id` | 기존 이어쓰기 주소. 기본은 상품 등록, 리뷰 종류를 지정하면 리뷰 작성으로 이동 |
| POST | `/submit_item_post` | 아래 상품 폼 필드 | 로그인 필요. HTML 등록 결과, 입력 오류 `400` |
| GET / POST | `/products/<product_id>/edit` | POST 상품 폼 필드. 사진 선택 | 상품 진행자 전용. 수정 폼 또는 관리로 이동 |
| GET | `/media/<image_id>` | — | 공유 이미지 바이너리 또는 `404` |

### 상품 폼

| 필드 | 규칙 |
| --- | --- |
| `name`, `price`, `address`, `status`, `email` | 필수. 가격은 0 이상 정수, 상태는 `new`, `lnew`, `used`. 판매자 ID는 세션 또는 기존 상품에서 결정 |
| `start_date`, `end_date`, `pickup_datetime` | 시작·마감일은 `YYYY-MM-DD` 필수. 한국 시간 기준 시작일은 오늘 이후 또는 수정 전과 같은 시작일. 마감일은 시작일 이상. 선택 수령 일시는 마감일 이상이며 ISO 분 단위 또는 `YYYY-MM-DD 오후 03:00` 형식 입력 가능 |
| `chat_url`, `buyer_chat_url` | 새 상품 문의 링크 필수, 구매자 링크 선택. 둘 다 `https://open.kakao.com/` 링크. 기존에 문의 링크가 없던 상품은 빈 값으로 수정 가능 |
| `file_input`, `category`, `target_count`, `description`, `manufacturer` | 신규 사진 필수. 분류는 생활 · 패션, 식품, 기타. 목표 수량 입력 시 양의 정수 |
| `size_enabled`, `sizes`, `color_enabled`, `colors` | 선택. 켠 옵션의 값을 줄 단위로 제출. 색상은 `이름` 또는 `이름\|#RRGGBB` |
| `custom_option_enabled`, `custom_option_name`, `custom_options` | 선택. 활성화하면 진행자가 지정하는 이름 하나와 줄 단위 선택지 필요. 선택지는 중복을 제거하고 최대 20개 저장 |

공개 상품 상세에는 `inquiry_chat_url`을, 주문 소유자가 보는 참여 완료·참여 상세에는 `buyer_chat_url`을 템플릿 컨텍스트로 제공합니다. 상품 상세에서 문의방을 열 수 있습니다. 기존 참여자용 링크는 공개 문의 링크로 전환되지 않습니다.

## 장바구니와 참여

| 메서드 | 경로 | 입력 | 응답 |
| --- | --- | --- | --- |
| GET | `/cart` | — | 장바구니와 합계 |
| POST | `/cart/add` | `product_id`, 선택지 `size`, `color`, `custom_option`, `quantity` | 장바구니로 이동. 동일 상품·옵션은 수량 합산. 마감 상품과 잘못된 선택은 상품 상세로 이동 |
| POST | `/cart/remove` | `index` (0부터 시작) | 장바구니로 이동 |
| POST | `/participate` | 단일 참여는 `product_id`, 옵션, `quantity`. 상품 ID 생략 시 장바구니 전체 | 로그인 필요. 참여 저장 후 완료 또는 마이페이지로 이동 |
| GET | `/order_done/<order_id>` | — | 주문 소유자의 참여 완료 화면 |
| GET | `/joined/<order_id>` | 쿼리 `tab=notice\|people\|contact` | 주문 소유자의 참여 상세 |

수량은 기본 1이며 1~99 범위로 제한합니다. 기타 옵션을 설정한 상품은 `custom_option` 값이 필수입니다. 선택값은 Firebase 주문에 저장합니다. 장바구니에서 참여할 때도 최신 선택지와 일치하는지 검사합니다.

## 리뷰

| 메서드 | 경로 | 입력 | 인증과 응답 |
| --- | --- | --- | --- |
| GET | `/review` | 쿼리 `product_id`, `sort=latest\|rating\|photo`, `page` | 공개 리뷰 목록 |
| GET | `/reviews/<id>`, `/review_detail?id=<id>` | 리뷰 ID | 공개 리뷰 상세 |
| GET / POST | `/reg_reviews` | 쿼리 또는 폼 `product_id`. POST `title`, `description`, `rating`(1~5), `file_input` | 참여자 전용. 상품 선택은 상품당 한 번 표시하고 최근 주문의 옵션을 사용. 성공 시 상세로 이동 |
| GET / POST | `/reviews/<id>/edit` | POST `title`, `description`, `rating`, 선택 사진 | 리뷰 작성자 전용. 수정 폼 또는 상세로 이동 |
| GET / POST | `/review_like/<review_id>` | POST JSON `{"liked":true}` 또는 `{"liked":false}` | 로그인 필요. JSON `{"liked":true}` 형태. 잘못된 값 `400`, 비로그인 `401`, 없는 리뷰 `404`, 저장소 장애 `503` |

## 진행자 관리와 문의

| 메서드 | 경로 | 입력 | 인증과 응답 |
| --- | --- | --- | --- |
| GET | `/manage/<product_id>` | 쿼리 `tab=info\|participants\|orders\|reviews\|qna\|notice`, `q`, `filter=all\|wait\|done`, `page` | 상품 진행자 전용 관리 화면 |
| POST | `/manage/<product_id>/notices` | `title`(80자 이하), `content`(5000자 이하), 선택 `important`, 수정 `edit_id` 또는 삭제 `delete` | 상품 진행자 전용. 공지 탭 또는 관리 화면으로 이동 |
| GET | `/manage/<product_id>/orders.csv` | — | 상품 진행자 전용. UTF-8 BOM CSV 첨부. 기타 옵션은 마지막 열 |
| POST | `/products/<id>/qna` | `question`(300자 이하), `category` | 로그인 필요. 문의 탭으로 이동 |
| POST | `/manage/<product_id>/qna` | `qna_id`, `answer`(300자 이하), 선택 `filter` | 상품 진행자 전용. 문의 관리로 이동 |

## Firebase 임시저장

로그인한 사용자의 종류별 최근 한 건을 `draft/{username}/{kind}`에 저장합니다. `kind`는 `product` 또는 `review`입니다. 상품 등록·리뷰 작성 폼과 마이페이지에서 이 API를 사용합니다. 게시 성공 시 제출한 버전과 같은 임시저장만 정리합니다.

| 메서드 | 경로 | 성공 응답 |
| --- | --- | --- |
| GET | `/api/drafts/<kind>` | `200`. 데이터가 없으면 `{"draft":null}` |
| PUT | `/api/drafts/<kind>` | `200`. 해당 종류를 한 건으로 저장하고 `draft` 객체 반환 |
| DELETE | `/api/drafts/<kind>` | `204`. 선택 쿼리 `version`을 지정하면 해당 버전만 삭제하며, 다른 버전으로 바뀐 경우 `409` |

상품 PUT은 상품 폼의 텍스트·숫자·체크박스 필드를 받습니다. 판매자 ID, 계산된 목표 금액과 사진은 제외합니다. 리뷰 PUT은 참여한 상품의 `product_id`와 선택 필드 `title`, `description`, `rating`을 받습니다. 요청은 최대 32 KiB입니다.

```json
{
  "draft": {
    "data": {"name": "공동구매 상품", "price": "12000"},
    "resume_url": "/reg_items",
    "updated_at": "2026-11-27T03:00:00+00:00"
  }
}
```

오류 응답은 `{"error":"메시지"}` 형식입니다. 입력 오류 `400`, 비로그인 `401`, 미참여 상품의 리뷰 임시저장 `403`, 지원하지 않는 종류 `404`, Firebase 장애 `503`을 반환합니다.
