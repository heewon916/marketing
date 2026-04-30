Open API 공통 가이드
HTTP API 공통
HTTP 요청 및 응답 Header
인증
인증을 위해 개발자 센터에서 발급한 API key pair를 사용합니다. HTTP 요청 header를 다음과 같이 지정해야 합니다.
x-access-key: <API Access Key>
x-secret-key: <API Secret Key>
요청 및 응답 형태
요청과 응답은 모두 Content-Type: application/json 형태여야 합니다.
응답 코드 및 Body 형태
응답 코드 : API가 성공적으로 응답할 시 응답 코드 200을 반환합니다. 응답 실패 시 실패 이유에 따라 401, 429, 500 등 상응하는 응답 코드를 반환합니다.
응답 형태 : 모든 HTTP API 응답 body는 기본적으로 아래 형태와 같습니다.
성공 응답


{
"resultType": "SUCCESS",
"success": <결과>
}
실패 응답


{
"resultType": "FAIL",
"error": {
"errorCode": "4010",
"reason": "에러 메시지",
"data": {/* ... */}
}
}
시각 (timestamp)
API 요청과 응답에 사용되는 모든 시각 (timestamp) 타입은 ISO 8601 형태(예: 2025-09-01T00:00:00Z)의 문자열입니다.

Pagination
너무 많은 정보를 한 번에 조회하지 않도록 목록 조회 시 페이지네이션을 사용합니다. 페이지 기반으로 목록을 조회할 수 있으며, page ,size , sortOrder 파라미터를 사용합니다.


GET https://open-api.tossplace.com/api-public/openapi/v1/merchants/{merchantId}/order/orders?page=1&size=100&sortOrder=DESC
page : 조회할 페이지입니다. 1페이지가 목록의 시작입니다.
size : 페이지의 크기입니다. 최소 1, 최대 500 값을 사용할 수 있으며 기본값은 100입니다.
sortOrder : 목록의 정렬 순서입니다. "ASC", "DESC" 값을 사용할 수 있습니다.
에러 처리
API 에러 응답은 HTTP 상태 코드와 함께 구체적인 에러 정보를 제공합니다.


{
"resultType": "FAIL",
"error": {
"errorCode": "4010",
"reason": "에러 메시지"
}
}
호출량 제한
Open API를 안정적으로 제공하기 위해 Open API의 시간당 호출량을 제한하고 있습니다. 허용된 호출량을 초과한 요청은 거부되며 HTTP 429 응답 코드를 반환합니다.


GET https://open-api.tossplace.com/api-public/openapi/v1/merchants/{merchantId}
x-access-key: YOUR_ACCESS_KEY
x-secret-key: YOUR_SECRET_KEY
Content-Type: application/json

HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 100
x-ratelimit-remaining: 0
x-ratelimit-reset: <timestamp>
위 예시처럼, HTTP 응답 header를 통해 호출량 제한에 관한 정보를 얻을 수 있습니다.

HTTP 응답 header	Type	설명	예시
x-ratelimit-limit	number	허용된 최대 호출량입니다.	100
x-ratelimit-remaining	number	이 요청 이후 남은 허용된 호출량입니다.	99
x-ratelimit-reset	timestamp (epoch milliseconds)	호출량 제한 초기화 시각으로, 이 시각 이후에 API를 더 호출할 수 있습니다.	1700000000000
호출량 제한은 Token Bucket 알고리즘으로 작동합니다.

Open API 호출 시 토큰을 1개 소비합니다. 토큰이 없는 경우 호출량 제한으로 인해 429 응답을 받습니다.
토큰은 1초당 10개씩 충전되며, 최대 100개까지 충전됩니다.
예시) Open API를 연속하여 호출하는 경우, 즉시 100개의 요청은 성공합니다. 이후 1초가 지나야 다음 10개 요청이 성공합니다.
x-ratelimit-remaining과 x-ratelimit-reset 응답 header를 통해 호출 주기를 조정하는 것을 권장합니다.
토큰은 매장별로 관리됩니다.
즉, 호출량 제한은 각 매장별로 적용됩니다. 특정 매장에 대한 요청에서 429 응답을 받더라도, 다른 매장에 대한 요청은 정상적으로 처리될 수 있습니다.
요청 추적
모든 Open API 응답은 x-toss-event-id HTTP 헤더를 포함합니다. 이 값은 요청 추적 및 문의 시 필요합니다.


GET https://open-api.tossplace.com/api-public/openapi/v1/merchants/{merchantId}
x-access-key: YOUR_ACCESS_KEY
x-secret-key: YOUR_SECRET_KEY
Content-Type: application/json

HTTP/1.1 200 OK
x-toss-event-id: <EVENT_ID>
// ...
Open API 사용 중 문의가 있으시다면, x-toss-event-id 헤더 값을 함께 제공해주세요. 기술 지원 중 개별 요청을 추적할 때 도움이 됩니다.

----

일반
Types
Open API 버전 (Version)
Name	Type	Required	Description	Example
version	String	✅	Open API 버전	"2026-03-31"
Methods
Open API 버전 정보 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/version
Response Type	Version
Description	Open API 버전 정보를 조회합니다.

----

Merchant API
매장의 기본 정보를 조회하는 API입니다. 매장명, 사업자등록번호 등 매장의 기본 정보를 확인할 수 있습니다.

Types
매장 (Merchant)
매장은 주문, 결제, 상품, 고객 관리 등 토스플레이스가 제공하는 서비스가 이루어지는 환경입니다. 매장은 보통 오프라인에서 하나의 사업장을 나타내며, 토스플레이스 Open API를 활용하여 매장이 보유한 데이터에 접근할 수 있습니다.

매장에서 앱을 설치하면, 앱에 등록된 key pair (access key와 secret key) 를 이용하여 매장의 데이터에 접근하는 Open API를 호출할 수 있습니다. 앱을 설치하지 않은 매장에 대해서는 API를 호출할 수 없습니다.

Name	Type	Required	Description	Example
id	Long	✅	매장 ID	42
name	String	✅	매장명	"플레이스 베이커리"
businessNumber	String	✅	사업자등록번호	"0000000000"
Methods
매장 정보 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}
Response Type	Merchant
Description	ID에 해당하는 매장 정보를 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
Events
매장 정보 변경됨
Property	Value
Event Type	merchant.merchant.updated.v1
Description	매장 정보가 변경되었습니다.
이벤트 Payload

Name	Type	Required	Description	Example
merchant	Merchant	✅	매장 정보
이벤트 Body 예시


{
"id": "000000000000000000000000",
"type": "merchant.merchant.updated.v1",
"createdAt": "2026-01-01T00:00:00.000Z",
"merchantId": 42,
"app": "my-awesome-app",
"data": {
"merchant": {
"id": 42,
"name": "플레이스 베이커리",
"businessNumber": "0000000000"
}
}
}

----

주문 복수건 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/order/orders/by-ids
Response Type	Order[]
Description	ID를 통해 매장의 주문 여러 건을 조회합니다. 최대 25건까지 조회 가능합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
ids	Query	String[]	✅	-	주문 ID 목록
주문 목록 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/order/orders
Response Type	Order[]
Description	매장의 주문 목록을 주문 생성 시각 순으로 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
from	Query	timestamp		-	조회 범위 시작점으로, 이 시점 이후에 생성된 주문만 조회합니다.
to	Query	timestamp		-	조회 범위 끝점으로, 이 시점 이전에 생성된 주문만 조회합니다.
orderStates	Query	OrderState[]		["COMPLETED", "CANCELLED"]	주문 상태 필터로, 파라미터로 주어진 값의 상태를 가지는 주문만 조회합니다.
sources	Query	String[]		-	주문 채널 필터로, 파라미터로 주어진 값의 주문 채널을 가지는 주문만 조회합니다.
page	Query	Int		1	조회할 페이지
size	Query	Int		100	페이지 크기
sortOrder	Query	SortOrder		"DESC"	정렬 순서 (주문 생성 시각 기준)

----

상품 (OrderItem)
Field	Type	Required	Description	Example
title	String	✅	상품명	"아메리카노"
code	String		상품 코드	""
category	OrderItemCategory	✅	상품이 속한 카테고리
상품 가격 (OrderItemPrice)
Name	Type	Required	Description	Example
title	String	✅	가격명	"기본"
priceType	OrderItemPriceType	✅	가격 종류	"FIXED"
priceUnit	Long	✅	가격 단위	1
priceValue	Long	✅	가격	3000
isTaxFree	Boolean	✅	면세 여부	false
taxPercentage	Int		세율	10
taxInclusive	Boolean	✅	부가세 포함 여부	true
상품 가격 종류 (OrderItemPriceType)
Value	Description
"FIXED"	정가
"VARIABLE"	시가
"UNIT"	단위가격
"UNDEFINED"
카테고리 (OrderItemCategory)
Field	Type	Required	Description	Example
title	String	✅	카테고리명	"커피"
code	String		카테고리 코드	""

----

주문 (Order)
주문은 매장에서 소비자가 상품을 구매하고 결제하는 것을 표현하는 개념입니다. 주문은 구매한 상품 목록, 결제 내역, 결제 금액 등 이 과정에서 기록되는 정보를 모두 포함하고 있습니다.

Field	Type	Required	Description	Example
id	String	✅	주문 ID	"620000000000000000"
merchantId	Long	✅	매장 ID	42
source	String	✅	주문이 인입된 경로	"POS"
orderState	OrderState	✅	주문 상태	"OPENED"
createdAt	timestamp	✅	생성 시각	"2025-09-01T00:00:00Z"
updatedAt	timestamp	✅	변경 시각	"2025-09-01T00:00:00Z"
openedAt	timestamp		주문 수락 시각	"2025-09-01T00:00:00Z"
completedAt	timestamp		주문 완료 시각	"2025-09-01T00:00:00Z"
cancelledAt	timestamp		주문 취소 시각	"2025-09-01T00:00:00Z"
lineItems	OrderLineItem[]	✅	주문 항목
payments	Payment[]	✅	결제 내역
discounts	Discount[]	✅	할인 내역
chargePrice	OrderChargePrice	✅	청구 금액

----

결제 단건 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/payment/payments/{paymentId}
Response Type	Payment
Description	매장의 결제 하나를 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
paymentId	Path	String	✅	-	결제 ID
주문의 결제건 모두 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/payment/payments/by-order-id
Response Type	Payment[]
Description	주문 하나의 결제 건을 모두 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
orderId	Query	String	✅	-	주문 ID

----

결제 (Payment)
결제 금액과 내역, 결제 수단별 세부 데이터를 포함하는 개념입니다.

Name	Type	Required	Description	Example
id	String	✅	결제 ID	"640000000000000000"
merchantId	Long	✅	매장 ID	42
orderId	String	✅	주문 ID	"620000000000000000"
state	PaymentState	✅	결제 상태	"APPROVED"
sourceType	PaymentSourceType	✅	결제수단 대분류	"CARD"
paymentMethod	String	✅	결제수단 세부 분류	"CARD_NFC"
van	String		VAN	"NICE"
amount	Long	✅	결제금액	3200
taxAmount	Long	✅	세액	291
supplyAmount	Long	✅	공급가액	2909
taxExemptAmount	Long	✅	면세금액	0
tipAmount	Long	✅	봉사료	0
approvedNo	String	✅	승인번호	"00000000"
approvedAt	timestamp		승인 시각	"2025-09-01T00:00:00Z"
cancelledAt	timestamp		취소 시각	"2025-09-01T00:00:00Z"
cashDetails	PaymentCashDetails		현금결제 세부 내역
cardDetails	PaymentCardDetails		카드결제 세부 내역
accountTransferDetails	PaymentAccountTransferDetails		계좌이체 세부 내역
easyPayDetails	PaymentEasyPayDetails		간편결제 세부 내역
externalDetails	PaymentExternalDetails		외부 결제수단 세부 내역
cashReceipt	PaymentCashReceipt		현금영수증 세부 내역
createdAt	timestamp	✅	생성 시각	"2025-09-01T00:00:00Z"
updatedAt	timestamp	✅	변경 시각	"2025-09-01T00:00:00Z"
결제 상태 (PaymentState)
Value	Description
"APPROVED"	승인됨
"CANCELLED"	취소됨
"UNDEFINED"

----

상품 (CatalogItem)
매장에 등록된 상품입니다. 소비자가 주문할 때 하나 또는 여러 상품을 주문에 포함하게 됩니다.

Name	Type	Required	Description	Example
id	String	✅	상품 ID	"42"
merchantId	Long	✅	매장 ID	42
title	String	✅	상품명	"아메리카노"
code	String		상품코드	""
description	String	✅	상품 설명	""
imageUrl	String		상품 이미지 URL	""
labels	String[]		상품 라벨 목록	["신규"]
price	CatalogItemPrice	✅	가격
createdAt	timestamp	✅	생성 시각	"2025-09-01T00:00:00Z"
updatedAt	timestamp	✅	수정 시각	"2025-09-01T00:00:00Z"
상품 가격 (CatalogItemPrice)
Name	Type	Required	Description	Example
title	String	✅	가격명	"기본"
priceType	CatalogItemPriceType	✅	가격 종류	"FIXED"
priceUnit	Long	✅	가격 단위	1
priceValue	Long	✅	가격	3000
barcode	String		바코드	""
상품 가격 종류 (CatalogItemPriceType)
Value	Description
"FIXED"	정가
"VARIABLE"	시가
"UNIT"	단위가격
"UNDEFINED"
Methods
상품 단건 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/catalog/items/{itemId}
Response Type	CatalogItem
Description	매장의 상품 하나를 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Description
merchantId	Path	Long	✅	매장 ID
itemId	Path	String	✅	상품 ID
상품 복수건 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/catalog/items/by-ids
Response Type	CatalogItem[]
Description	ID를 통해 매장의 상품 여러 건을 조회합니다. 최대 25건까지 조회 가능합니다.
요청 파라미터

Parameter	Location	Type	Required	Description
merchantId	Path	Long	✅	매장 ID
ids	Query	String[]	✅	상품 ID 목록
상품 목록 조회
Property	Value
Method	GET
Path	/api-public/openapi/v1/merchants/{merchantId}/catalog/items
Response Type	CatalogItem[]
Description	매장의 상품 목록을 상품 ID 순으로 조회합니다.
요청 파라미터

Parameter	Location	Type	Required	Default	Description
merchantId	Path	Long	✅	-	매장 ID
page	Query	Int		1	조회할 페이지
size	Query	Int		100	페이지 크기
