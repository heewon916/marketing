-- =============================================================
--  SEED DATA: maketing schema
--  사용자: 99jiseon@gmail.com (이메일 컬럼 없음 — 주석으로만 기록)
--  스토어: 키에리 (서울 용산구 이태원로26길 16-8)
--  인스타그램: @hmmnyanyam_
-- =============================================================
SET search_path TO maketing;



-- ----------------------------------------------------
-- 1. users
-- ----------------------------------------------------
INSERT INTO maketing.users (
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
    'hmmnyanyam_',   -- 실제 Instagram numeric ID로 교체 필요
    'hmmnyanyam_',
    NULL,
    NULL,
    FALSE,
    NOW(),
    NOW()
);

-- ----------------------------------------------------
-- 2. stores
-- ----------------------------------------------------
INSERT INTO maketing.stores (
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
    '키에리',
    '제과점',
    'aesthetic',
    '서울특별시 용산구 이태원로26길 16-8',
    37.5349660,
    126.9941570,
    '{
        "mon": {"open":"12:30","close":"20:30","last_order":"20:00"},
        "tue": null,
        "wed": null,
        "thu": {"open":"12:30","close":"20:30","last_order":"20:00"},
        "fri": {"open":"12:30","close":"20:30","last_order":"20:00"},
        "sat": {"open":"12:30","close":"21:00","last_order":"20:30"},
        "sun": {"open":"12:30","close":"20:30","last_order":"20:00"}
    }',
    NOW(),
    NOW()
);

-- ----------------------------------------------------
-- 3. store_hours  (화·수 정기휴무 → NULL)
-- ----------------------------------------------------
INSERT INTO maketing.store_hours (
    store_id,
    monday_open,    monday_close,
    tuesday_open,   tuesday_close,
    wednesday_open, wednesday_close,
    thursday_open,  thursday_close,
    friday_open,    friday_close,
    saturday_open,  saturday_close,
    sunday_open,    sunday_close
) VALUES (
    '663c31d7-87c6-4b83-bc0b-756e84a7a3a7',
    '12:30', '20:30',   -- 월
    NULL,    NULL,       -- 화 (정기휴무)
    NULL,    NULL,       -- 수 (정기휴무)
    '12:30', '20:30',   -- 목
    '12:30', '20:30',   -- 금
    '12:30', '21:00',   -- 토
    '12:30', '20:30'    -- 일
);

-- ----------------------------------------------------
-- 4. menus
-- ----------------------------------------------------
-- 케이크·디저트 (가격 변동 → NULL)
INSERT INTO maketing.menus (id, store_id, name, price, description, created_at, updated_at) VALUES
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '피스타치오티라미슈',           NULL, '직접 만드는 피스타치오스프레드와 구운피스타치오가 가득! 키에리만의 특별한 티라미슈입니다.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '하동말차티라미슈',             NULL, '하동말차로 만드는 키에리만의 스타일! 티라미슈입니다.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '촉촉 초코보스턴크림케이크',    NULL, '촉촉한 노버터 초콜릿케이크와 홈메이드보스턴크림', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '말차딸기시트케이크',           NULL, '촉촉하고 진한 말차시트와 (노버터) 수제딸기크림이 가득한 5호사이즈 조각케이크입니다.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '애플크럼블케이크',             NULL, '경북부사를 듬뿍 넣어 구운 사과크럼블케이크. 홈메이드캬라멜우유소스를 곁들여 먹는 케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '밤호박치즈케이크',             NULL, '제철 국내산 당도높은 미니밤호박을 사용해 만드는 치즈케이크입니다.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '바나나케이크',                 NULL, '바나나를 노버터시트와 크림에 넣어 촉촉하고 향긋한 티케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '얼그레이블랙티케이크',         NULL, 'Earl Grey & Afternoon Breakfast 잎차를 우려넣은 진한 티케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '바나나흑임자케이크',           NULL, '바나나시트에 흑임자스프레드가 레이어드된 시트케이크입니다.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '블루베리티라미슈',             NULL, '노버터 카카오 크럼블과 키에리만의 특별한 티라미슈크림에 홈메이드 블루베리콤포트의 만남', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '홈메이드유자티라미슈',         NULL, '홈메이드노버터크럼블과 1년숙성 고흥유자, 수제티라미슈크림', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '밤호박라떼크림케이크',         NULL, '밤호박노버터시트와 유기농에스프레소샷이 들어간 라떼크림 샌드케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '수분가득 말차딸기크림케이크',  NULL, '수분가득 촉촉한 하동말차노버터시트와 홈메이드딸기크림', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '밤호박라떼크림 트라이플케이크',NULL, '밤호박노버터시트와 유기농에스프레소샷을 넣은 홈메이드크림', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '초코트리플베리 트라이플케이크',NULL, '노버터초콜릿시트와 홈메이드트리플베리콤포트 홈메이드 크림', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '콘크럼블치즈케이크',          NULL, '옥수수치즈케이크와 바삭한 노버터 크럼블 가득한 케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '뽕베리레이어드치즈케이크',    NULL, '3월부터 6월까지만 나오는 봄스페셜케이크!', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '쑥팥치즈케이크',              NULL, '인진쑥치즈케이크와 우리팥크림의 만남. 6월까지 시즌운영.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '헤이즐넛초콜릿치즈케이크',    NULL, '구운 헤이즐넛과 초콜릿치즈케이크. 고소하고 담백!', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '흑미콩크림쌀케이크',          NULL, '흑미쌀 제누와즈와 고소한 콩크림 / 노버터 쌀케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '애플크럼블치즈케이크',        NULL, '노버터 크럼블 위에 진한 치즈케이크, 그위에 사과와 크럼블 듬뿍! 시나몬·버터 미사용.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '단호박치즈케이크',            NULL, '단호박을 직접 찌고 다져서 치즈케이크에 듬뿍넣은 구황작물치즈케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '할머니의케이크',              NULL, '현미쌀시트와 캐슈넛크림 / 퍽퍽한 식감이 매력적인 고소한 쌀케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '피넛버터초콜릿케이크',        NULL, '초콜릿시트와 피넛버터크림! 고소하고 단맛이 강하지 않아 남녀노소 인기있는 디저트', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '리틀데블스케이크',            NULL, '다크초콜릿시트와 진한 초콜릿크림. 노버터초콜릿케이크.', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '고르곤졸라치즈케이크',        NULL, '이탈리아 고르곤졸라치즈를 넣어 꼬릿한 향이 매력적인 치즈케이크. 따뜻한 화이트초콜릿과 함께!', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '꿀고구마치즈케이크',          NULL, '고구마를 삶고 으깨어 듬뿍넣은 고구마 치즈케이크 / 시즌케이크', NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '에그타르트',                  NULL, '버터를 안넣은 파이지와 바닐라빈 듬뿍들어간 달걀필링! 주말 스페셜 메뉴', NOW(), NOW()),
-- 커피·음료 (고정 가격)
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '아메리카노',      5600, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '카페라떼',        5900, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '카페모카',        5900, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '카라멜마끼아또',  5900, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '두유라떼',        5900, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '콜드브루',        6000, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '콜드브루라떼',    6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '소리라떼',        5800, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '코코넛 커피',     6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '바닐라 라떼',     6000, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '녹차라떼',        6000, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '초콜릿라떼',      6000, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '민트초코라떼',    6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '카모마일티',      6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '페퍼민트티',      6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '히비스커스티',    6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '루이보스티',      6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '자스민플라워티',  6500, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '로얄밀크티',      7000, NULL, NOW(), NOW()),
(gen_random_uuid(), '663c31d7-87c6-4b83-bc0b-756e84a7a3a7', '타로밀크티',      7000, NULL, NOW(), NOW());

-- ----------------------------------------------------
-- 5. holidays  (취급 이벤트일 기준 2025~2026)
-- ----------------------------------------------------
INSERT INTO maketing.holidays (id, holiday_date, name, created_at) VALUES
(gen_random_uuid(), '2025-01-29', '설날',        NOW()),
(gen_random_uuid(), '2026-02-17', '설날',        NOW()),
(gen_random_uuid(), '2025-02-14', '발렌타인데이', NOW()),
(gen_random_uuid(), '2026-02-14', '발렌타인데이', NOW()),
(gen_random_uuid(), '2025-03-14', '화이트데이',  NOW()),
(gen_random_uuid(), '2026-03-14', '화이트데이',  NOW()),
(gen_random_uuid(), '2025-05-05', '어린이날',    NOW()),
(gen_random_uuid(), '2026-05-05', '어린이날',    NOW()),
(gen_random_uuid(), '2025-05-08', '어버이날',    NOW()),
(gen_random_uuid(), '2026-05-08', '어버이날',    NOW()),
(gen_random_uuid(), '2025-10-06', '추석',        NOW()),
(gen_random_uuid(), '2026-09-25', '추석',        NOW()),
(gen_random_uuid(), '2025-12-25', '크리스마스',  NOW()),
(gen_random_uuid(), '2026-12-25', '크리스마스',  NOW());