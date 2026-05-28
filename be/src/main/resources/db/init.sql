-- =============================================================
--  LOCAL INIT DATA
--  목적: 로컬/Postman 테스트에서 stores가 비어 있어도
--       /api/v1/contents/caption 날씨 컨텍스트 API를 바로 검증할 수 있게 한다.
--  주의: JPA ddl-auto=update가 만든 기본 public schema 테이블 기준이다.
-- =============================================================

INSERT INTO users (
    id,
    instagram_user_id,
    instagram_username,
    access_token,
    token_expires_at,
    camera_mic_granted,
    created_at,
    updated_at
) VALUES (
    '5ba9f568-807c-42ef-b2a8-01b95193a1b4',
    'local_weather_test_user',
    'local_weather_test_user',
    NULL,
    NULL,
    FALSE,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    instagram_user_id = EXCLUDED.instagram_user_id,
    instagram_username = EXCLUDED.instagram_username,
    updated_at = NOW();

INSERT INTO stores (
    id,
    user_id,
    merchant_id,
    store_name,
    category,
    owner_persona,
    address,
    latitude,
    longitude,
    operating_hours,
    created_at,
    updated_at
) VALUES (
    '663c31d7-87c6-4b83-bc0b-756e84a7a3a7',
    '5ba9f568-807c-42ef-b2a8-01b95193a1b4',
    NULL,
    '로컬 테스트 매장',
    '카페',
    'aesthetic',
    '서울특별시 중구 세종대로 110',
    37.5665000,
    126.9780000,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    store_name = EXCLUDED.store_name,
    category = EXCLUDED.category,
    owner_persona = EXCLUDED.owner_persona,
    address = EXCLUDED.address,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    updated_at = NOW();
