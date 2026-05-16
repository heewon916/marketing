# 크롤러 고도화: POS 메뉴와 네이버 플레이스 메뉴 설명 매칭 구현 계획

## 1. 개요
토스 POS로부터 가져온 신뢰도 높은 '메뉴명 및 가격' 데이터에, 네이버 플레이스에서 크롤링한 '메뉴 설명(Description)' 데이터를 결합하여 고품질의 메뉴 정보를 구축합니다. 이미 DB의 `menus` 테이블에 존재하는 `description` 컬럼을 활용하여 데이터를 채워 넣는 방식으로 동작합니다. 이를 통해 이후 AI 분석 및 인스타그램 포스팅 시 더 풍부한 컨텍스트를 제공할 수 있습니다.

## 2. 작업 상세 계획

### 2.1. 크롤러 기능 고도화 (`crawler/naver_map_menu_hours.py`)
현재 장소 상세 조회 API(`/api/place/{place_id}`)는 영업시간만 반환하고 있습니다. 여기에 메뉴 크롤링 로직을 추가합니다.
- **수정 위치:** `get_place_detail` 엔드포인트 함수 내부
- **작업 내용:** 
  - 메뉴 탭(`/menu`)의 데이터를 가져오기 위해 기존에 정의된 `fetch_menu_tab_data`와 `build_menus_with_candidates`를 호출합니다.
  - 파싱된 메뉴 목록(`menu_name`, `price`, `menu_description` 포함)을 응답의 `data.menus` 필드에 포함시켜 반환하도록 구조를 변경합니다.

### 2.2. 백엔드 DTO 및 Entity 확장
클라이언트로부터 네이버 플레이스 고유 ID를 전달받고, 엔티티의 설명을 수정할 수 있는 기반 코드를 마련합니다.
- **수정 위치 1:** `be/src/main/java/com/matketing/be/domain/onboarding/dto/StoreUpdateRequest.java`
  - **작업 내용:** 크롤러 조회를 위한 식별자인 `placeId` 필드를 추가합니다.
- **수정 위치 2:** `be/src/main/java/com/matketing/be/domain/store/entity/Menu.java`
  - **작업 내용:** 이미 존재하는 `description` 필드를 안전하게 갱신할 수 있도록 `updateDescription(String description)` 편의 메서드를 추가합니다.
- **수정 위치 3:** `be/src/main/java/com/matketing/be/domain/store/repository/MenuRepository.java`
  - **작업 내용:** 상점 ID로 등록된 기존 메뉴들을 조회하여 매칭에 사용할 수 있도록 `List<Menu> findByStoreId(UUID storeId)` 쿼리 메서드를 추가합니다.

### 2.3. 매칭 및 병합 비즈니스 로직 구현 (`OnboardingService.java`)
상점 데이터를 업데이트하거나 동기화하는 시점에, 두 출처의 데이터를 매칭하여 설명을 병합합니다.
- **수정 위치:** `be/src/main/java/com/matketing/be/domain/onboarding/service/OnboardingService.java` (`updateStoreData` 메서드 중심)
- **작업 내용:**
  1. 클라이언트 요청(Request)에 `placeId`가 포함되어 전달되면, 크롤러 프록시 메서드(`getPlaceDetailViaCrawler`)를 호출하여 네이버 플레이스의 상세 정보(메뉴 목록 포함)를 가져옵니다.
  2. `MenuRepository.findByStoreId`를 통해 DB에 저장되어 있는 기존(Toss 기반) 메뉴 목록 영속성 객체를 불러옵니다.
  3. **이름 기반 정규화 매칭 알고리즘:** 네이버 플레이스에서 가져온 메뉴명과 DB 메뉴명을 비교합니다. 
     - 띄어쓰기 및 영어 대소문자 차이로 인한 매칭 실패를 방지하기 위해 텍스트를 정규화(`replaceAll("\\s+", "").toLowerCase()`)하여 일치 여부를 판단합니다.
  4. 이름이 매칭된 메뉴 중에서 네이버 플레이스 데이터에 `menu_description`이 존재하고 비어있지 않다면, 해당 DB 엔티티의 `updateDescription`을 호출하여 설명을 주입합니다.
  5. 스프링 트랜잭션(`@Transactional`) 종료 시 영속성 컨텍스트의 Dirty Checking 메커니즘에 의해 DB의 `description` 컬럼에 UPDATE 쿼리가 자동 발생되어 반영됩니다.

## 3. 기대 효과
- Toss POS 데이터의 약점(사용자가 메뉴 설명을 잘 입력해 두지 않아 누락 빈번함)을 네이버 지도 데이터로 보완합니다.
- "맡케팅" 시스템의 핵심인 AI 포스팅 캡션 생성 시, 메뉴에 대한 자세한 설명을 컨텍스트로 제공함으로써 훨씬 더 매력적이고 구체적인 마케팅 문구(예: 메뉴의 맛, 재료, 식감 등) 생성이 가능해집니다.