# 외부 API 연동 안정성 고도화: 서킷 브레이커 및 Retry 도입 계획

## 1. 개요
현재 토스(Toss) POS 연동, 네이버 플레이스 크롤러 서버, 인스타그램 Graph API 등 외부 시스템과 동기적(Synchronous)으로 통신하고 있습니다. 외부 서버에 장애가 발생하거나 응답 지연(Timeout)이 발생할 경우, 우리 백엔드 서버의 스레드(Thread)가 계속 대기 상태에 빠지게 되어 연쇄 장애(Cascading Failure)로 이어질 위험이 있습니다.
이를 방지하기 위해 **Resilience4j** 라이브러리를 도입하여 **서킷 브레이커(Circuit Breaker)**와 **재시도(Retry)** 매커니즘을 적용하고, 안정적인 서비스 가용성을 확보합니다.

## 2. 작업 상세 계획

### 2.1. 의존성 추가 (`build.gradle`)
Resilience4j와 Spring AOP 의존성을 추가하여 어노테이션 기반으로 서킷 브레이커를 적용할 수 있도록 구성합니다.
- `org.springframework.boot:spring-boot-starter-aop`
- `io.github.resilience4j:resilience4j-spring-boot3`

### 2.2. Resilience4j 설정 (`application.yml` 등)
외부 호출 특성에 맞게 서킷 브레이커와 Retry 정책을 전역 또는 인스턴스별로 세밀하게 설정합니다.
- **Circuit Breaker 설정:**
  - `sliding-window-size`: 서킷의 상태를 평가할 최근 호출 횟수 (예: 10회)
  - `failure-rate-threshold`: 실패율 임계치 (예: 50% 이상 실패 시 서킷 Open)
  - `wait-duration-in-open-state`: 서킷이 차단(Open) 상태로 유지되는 시간 (이후 Half-Open으로 전환, 예: 10초)
- **Retry 설정:**
  - `max-attempts`: 최대 재시도 횟수 (예: 3회)
  - `wait-duration`: 재시도 간 기본 대기 시간 (예: 1초, 지수 백오프 적용 가능)

### 2.3. 서비스 계층 적용 (`OnboardingService.java` 등)
외부 API를 호출하는 메서드에 서킷 브레이커와 재시도 로직을 적용하고, 장애 발생 시 안전하게 응답할 Fallback 메서드를 작성합니다.
- **적용 대상 메서드:**
  - `fetchMenusFromToss` (토스 메뉴 조회)
  - `getMerchantNameFromToss` (토스 매장명 조회)
  - `searchPlacesViaCrawler` / `getPlaceDetailViaCrawler` (크롤러 연동)
- **어노테이션 적용:**
  - 대상 메서드에 `@CircuitBreaker(name = "tossApi", fallbackMethod = "fallbackTossApi")` 및 `@Retry(name = "tossApi")` 적용
- **Fallback 메서드 구현:**
  - 서킷이 Open되어 호출이 즉시 차단되거나 최종적으로 재시도에 실패했을 때 실행되는 메서드입니다.
  - 사용자에게 예외를 던지거나, 빈 리스트(`Collections.emptyList()`)를 반환하여 로직이 중단되지 않고 유연하게 넘어갈 수 있도록 처리합니다.

## 3. 기대 효과
- **장애 전파 차단 (Fault Tolerance):** 외부 시스템(토스, 크롤러) 장애 시 빠른 실패(Fast Fail)를 유도하여 백엔드 스레드 고갈 및 서버 다운을 방지합니다.
- **가용성 향상:** 일시적인 네트워크 순단이나 오류에 대해 자동으로 재시도(Retry)하여 성공 확률을 높입니다.
- **안정적인 UX 제공:** Fallback 처리를 통해 무한 로딩 대신 "현재 외부 서비스 지연이 발생하고 있습니다" 등 상황에 맞는 유연한 에러 핸들링이 가능해집니다.