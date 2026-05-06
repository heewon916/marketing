-- =============================================================
--  SCHEMA: maketing
-- =============================================================
CREATE SCHEMA IF NOT EXISTS maketing;
SET search_path TO maketing;

-- =============================================================
--  ENUM TYPES
-- =============================================================
CREATE TYPE maketing.category_type AS ENUM (
    '주점',
    '제과점',
    '카페',
    '식당'
);

CREATE TYPE maketing.owner_persona_type AS ENUM (
    'aesthetic', 'friendly', 'professional', 'trendy', 'other'
);

-- =============================================================
--  USERS
-- =============================================================
CREATE TABLE maketing.users (
    "id"                  UUID          NOT NULL,
    "instagram_user_id"   VARCHAR(100)  NOT NULL,
    "instagram_username"  VARCHAR(100)  NULL,
    "access_token"        TEXT          NULL,
    "token_expires_at"    TIMESTAMPTZ   NULL,
    "camera_mic_granted"  BOOLEAN       NULL,
    "created_at"          TIMESTAMPTZ   NULL,
    "updated_at"          TIMESTAMPTZ   NULL,
    CONSTRAINT "PK_USERS" PRIMARY KEY ("id")
);

-- =============================================================
--  STORES
-- =============================================================
CREATE TABLE maketing.stores (
    "id"               UUID                        NOT NULL,
    "user_id"          UUID                        NOT NULL,
    "merchant_id"      VARCHAR(20)                 NULL,
    "store_name"       VARCHAR(200)                NOT NULL,
    "category"         maketing.category_type      NULL,
    "owner_persona"    maketing.owner_persona_type NULL,
    "address"          TEXT                        NULL,
    "latitude"         DECIMAL(10, 7)              NULL,
    "longitude"        DECIMAL(10, 7)              NULL,
    "operating_hours"  JSONB                       NULL,
    "created_at"       TIMESTAMPTZ                 NULL,
    "updated_at"       TIMESTAMPTZ                 NULL,
    CONSTRAINT "PK_STORES" PRIMARY KEY ("id"),
    CONSTRAINT "FK_users_TO_stores"
        FOREIGN KEY ("user_id") REFERENCES maketing.users ("id")
);

COMMENT ON COLUMN maketing.stores."operating_hours" IS '영업시간';

-- =============================================================
--  STORE_HOURS
-- =============================================================
CREATE TABLE maketing.store_hours (
    "store_id"         UUID  NOT NULL,
    "monday_open"      TIME  NULL,
    "tuesday_open"     TIME  NULL,
    "wednesday_open"   TIME  NULL,
    "thursday_open"    TIME  NULL,
    "friday_open"      TIME  NULL,
    "saturday_open"    TIME  NULL,
    "sunday_open"      TIME  NULL,
    "monday_close"     TIME  NULL,
    "tuesday_close"    TIME  NULL,
    "wednesday_close"  TIME  NULL,
    "thursday_close"   TIME  NULL,
    "friday_close"     TIME  NULL,
    "saturday_close"   TIME  NULL,
    "sunday_close"     TIME  NULL,
    CONSTRAINT "PK_STORE_HOURS" PRIMARY KEY ("store_id"),
    CONSTRAINT "FK_stores_TO_store_hours"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  MENUS
-- =============================================================
CREATE TABLE maketing.menus (
    "id"            UUID          NOT NULL,
    "store_id"      UUID          NOT NULL,
    "name"          VARCHAR(200)  NOT NULL,
    "price"         INTEGER       NULL,
    "description"   TEXT          NULL,
    "weather_tags"  JSONB         DEFAULT '' NULL,
    "holiday_tags"  JSONB         DEFAULT '' NULL,
    "created_at"    TIMESTAMPTZ   NULL,
    "updated_at"    TIMESTAMPTZ   NULL,
    "embedding"     VECTOR(1536)  NULL,
    CONSTRAINT "PK_MENUS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_menus"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  HOLIDAYS
-- =============================================================
CREATE TABLE maketing.holidays (
    "id"            UUID          NOT NULL,
    "holiday_date"  DATE          NOT NULL,
    "name"          VARCHAR(200)  NOT NULL,
    "created_at"    TIMESTAMPTZ   NULL,
    CONSTRAINT "PK_HOLIDAYS" PRIMARY KEY ("id")
);

-- =============================================================
--  DEVICE_TOKENS
-- =============================================================
CREATE TABLE maketing.device_tokens (
    "id"          UUID         NOT NULL,
    "user_id"     UUID         NOT NULL,
    "token"       TEXT         NULL,
    "platform"    VARCHAR      NULL,
    "is_active"   BOOLEAN      NULL,
    "created_at"  TIMESTAMPTZ  NULL,
    "updated_at"  TIMESTAMPTZ  NULL,
    CONSTRAINT "PK_DEVICE_TOKENS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_users_TO_device_tokens"
        FOREIGN KEY ("user_id") REFERENCES maketing.users ("id")
);

-- =============================================================
--  API_TOKEN_LOGS
-- =============================================================
CREATE TABLE maketing.api_token_logs (
    "id"             UUID         NOT NULL,
    "user_id"        UUID         NOT NULL,
    "old_expires_at" TIMESTAMPTZ  NULL,
    "new_expires_at" TIMESTAMPTZ  NULL,
    "created_at"     TIMESTAMPTZ  NULL,
    CONSTRAINT "PK_API_TOKEN_LOGS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_users_TO_api_token_logs"
        FOREIGN KEY ("user_id") REFERENCES maketing.users ("id")
);

-- =============================================================
--  CONTENTS
-- =============================================================
CREATE TABLE maketing.contents (
    "id"                   BIGINT        NOT NULL,
    "store_id"             UUID          NOT NULL,
    "session_id"           UUID          NULL,
    "caption"              TEXT          NULL,
    "instagram_media_id"   VARCHAR(100)  NULL,
    "instagram_permalink"  TEXT          NULL,
    "published_at"         TIMESTAMPTZ   NULL,
    "is_deleted"           BOOLEAN       NULL,
    "deleted_at"           TIMESTAMPTZ   NULL,
    "created_at"           TIMESTAMPTZ   NULL,
    CONSTRAINT "PK_CONTENTS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_contents"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  CONTENTS_IMAGES
-- =============================================================
CREATE TABLE maketing.contents_images (
    "id"           UUID          NOT NULL,
    "contents_id"  BIGINT        NOT NULL,
    "s3_key"       VARCHAR(200)  NOT NULL,
    CONSTRAINT "PK_CONTENTS_IMAGES" PRIMARY KEY ("id"),
    CONSTRAINT "FK_contents_TO_contents_images"
        FOREIGN KEY ("contents_id") REFERENCES maketing.contents ("id")
);

-- =============================================================
--  VIDEO_RECORDINGS
-- =============================================================
CREATE TABLE maketing.video_recordings (
    "id"           UUID          NOT NULL,
    "contents_id"  BIGINT        NOT NULL,
    "s3_key"       VARCHAR(200)  NOT NULL,
    CONSTRAINT "PK_VIDEO_RECORDINGS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_contents_TO_video_recordings"
        FOREIGN KEY ("contents_id") REFERENCES maketing.contents ("id")
);

-- =============================================================
--  INSTAGRAM_METRICS
-- =============================================================
CREATE TABLE maketing.instagram_metrics (
    "id"                   UUID          NOT NULL,
    "contents_id"          BIGINT        NULL,
    "store_id"             UUID          NOT NULL,
    "instagram_media_id"   VARCHAR(100)  NOT NULL,
    "reaches"              INTEGER       NULL,
    "saves"                INTEGER       NULL,
    "shares"               INTEGER       NULL,
    "likes"                INTEGER       NULL,
    "created_at"           TIMESTAMPTZ   NULL,
    CONSTRAINT "PK_INSTAGRAM_METRICS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_contents_TO_instagram_metrics"
        FOREIGN KEY ("contents_id") REFERENCES maketing.contents ("id"),
    CONSTRAINT "FK_stores_TO_instagram_metrics"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  UPLOAD_HISTORY
-- =============================================================
CREATE TABLE maketing.upload_history (
    "id"             UUID        NOT NULL,
    "store_id"       UUID        NOT NULL,
    "uploaded_at"    TIMESTAMPTZ NOT NULL,
    "uploaded_date"  DATE        NULL,
    "day_of_week"    SMALLINT    NOT NULL,
    "created_at"     TIMESTAMPTZ NULL,
    CONSTRAINT "PK_UPLOAD_HISTORY" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_upload_history"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  UPLOAD_PATTERNS
-- =============================================================
CREATE TABLE maketing.upload_patterns (
    "id"              UUID        NOT NULL,
    "store_id"        UUID        NOT NULL,
    "day_of_week"     SMALLINT    NOT NULL,
    "predicted_time"  TIME        NULL,
    "sample_count"    INTEGER     NULL,
    "last_updated"    TIMESTAMPTZ NULL,
    CONSTRAINT "PK_UPLOAD_PATTERNS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_upload_patterns"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  ACCOUNT_WEEKLY_METRICS
-- =============================================================
CREATE TABLE maketing.account_weekly_metrics (
    "id"                  UUID            NOT NULL,
    "store_id"            UUID            NOT NULL,
    "total_reach"         INTEGER         NULL,
    "target_post_count"   INTEGER         NULL,
    "actual_post_count"   INTEGER         NULL,
    "achievement_rate"    DECIMAL(5, 2)   NULL,
    "visit_intent_score"  INTEGER         NULL,
    "created_at"          TIMESTAMPTZ     NULL,
    "is_deleted"          BOOLEAN         NULL,
    CONSTRAINT "PK_ACCOUNT_WEEKLY_METRICS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_account_weekly_metrics"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  NOTIFICATIONS
-- =============================================================
CREATE TABLE maketing.notifications (
    "id"              UUID         NOT NULL,
    "store_id"        UUID         NOT NULL,
    "notification"    TEXT         NULL,
    "scheduled_at"    TIMESTAMPTZ  NULL,
    "created_at"      TIMESTAMPTZ  NULL,
    "type"            SMALLINT     NULL,
    "status"          SMALLINT     NULL,
    "sent_at"         TIMESTAMPTZ  NULL,
    "updated_at"      TIMESTAMPTZ  NULL,
    "retry_count"     INTEGER      NULL,
    "failure_reason"  TEXT         NULL,
    "web_url"         TEXT         NULL,
    "reference_id"    UUID         NULL,
    CONSTRAINT "PK_NOTIFICATIONS" PRIMARY KEY ("id"),
    CONSTRAINT "FK_stores_TO_notifications"
        FOREIGN KEY ("store_id") REFERENCES maketing.stores ("id")
);

-- =============================================================
--  CANONICAL_KEYWORDS
-- =============================================================
CREATE TABLE maketing.canonical_keywords (
    "id"            BIGINT        NOT NULL,
    "code"          VARCHAR(100)  NULL,
    "display_name"  VARCHAR(200)  NOT NULL,
    "embedding"     VECTOR(1536)  NOT NULL,
    "created_at"    TIMESTAMPTZ   NOT NULL,
    CONSTRAINT "PK_CANONICAL_KEYWORDS" PRIMARY KEY ("id")
);

COMMENT ON COLUMN maketing.canonical_keywords."display_name" IS '사용자/운영자가 읽는 표시 이름';
COMMENT ON COLUMN maketing.canonical_keywords."embedding"    IS '표준 키워드 임베딩 벡터 (pgvector 코사인 유사도 검색용)';

-- =============================================================
--  REFERENCE_CAPTIONS
-- =============================================================
CREATE TABLE maketing.reference_captions (
    "id"               BIGINT        NOT NULL,
    "caption_content"  TEXT          NOT NULL,
    "embedding"        VECTOR(1536)  NOT NULL,
    CONSTRAINT "PK_REFERENCE_CAPTIONS" PRIMARY KEY ("id")
);

-- =============================================================
--  REFERENCE_IMAGES
-- =============================================================
CREATE TABLE maketing.reference_images (
    "id"                       BIGINT        NOT NULL,
    "sort_order"               SMALLINT      NULL,
    "s3_key"                   VARCHAR(200)  NOT NULL,
    -- 피사체
    "focus_subject"            VARCHAR(100)  NULL,
    "focus_subject_embedding"  VECTOR(1536)  NULL,
    -- 촬영 구도
    "shot_type"                VARCHAR(20)   NULL,
    "shot_type_code"           VARCHAR(50)   NULL,
    "shot_type_embedding"      VECTOR(1536)  NULL,
    -- 카메라 앵글
    "camera_angle"             VARCHAR(20)   NULL,
    "camera_angle_code"        VARCHAR(50)   NULL,
    "camera_angle_embedding"   VECTOR(1536)  NULL,
    -- 스타일/필터
    "style_filter"             VARCHAR(100)  NULL,
    -- 조명
    "lighting_params"          JSONB         NULL,
    CONSTRAINT "PK_REFERENCE_IMAGES" PRIMARY KEY ("id")
);

COMMENT ON COLUMN maketing.reference_images."shot_type" IS
'원본 텍스트 보존. 정규화 코드는 shot_type_code 사용.
shot_type_code 허용값: closeup | macro_detail | tabletop_medium | wide_full | flat_lay';

COMMENT ON COLUMN maketing.reference_images."camera_angle" IS
'원본 텍스트 보존. 정규화 코드는 camera_angle_code 사용.
camera_angle_code 허용값: top_90 | high_60 | high_45 | high_30 | eye_level | dutch_angle | low_angle | worm_eye';

COMMENT ON COLUMN maketing.reference_images."style_filter" IS
'예: 하이 컨트라스트/비비드, 페이디드/빈티지, 다크 시네마틱, 브라이트 앤 에어리, 앤 코지';

COMMENT ON COLUMN maketing.reference_images."lighting_params" IS
'표준 키:
  type       → lowkey | softlight | natural | highlight
  direction  → front | side | back | top | spot
  color_temp → warm | cool | neutral
  mood       → cinematic | airy | moody | cozy
예시: {"type":"lowkey","direction":"spot","color_temp":"cool","mood":"cinematic"}';

-- =============================================================
--  REFERENCE  (포스트 단위 캡션-이미지 연결)
-- =============================================================
CREATE TABLE maketing.reference (
    "id"             BIGINT                      NOT NULL,
    "caption_id"     BIGINT                      NOT NULL,
    "image_id"       BIGINT                      NOT NULL,
    "owner_persona"  maketing.owner_persona_type NULL,
    "store_name"     VARCHAR(200)                NULL,
    "created_at"     DATE                        NULL,
    "instagram_id"   VARCHAR(200)                NULL,
    CONSTRAINT "PK_REFERENCE" PRIMARY KEY ("id"),
    CONSTRAINT "FK_reference_captions_TO_reference"
        FOREIGN KEY ("caption_id") REFERENCES maketing.reference_captions ("id"),
    CONSTRAINT "FK_reference_images_TO_reference"
        FOREIGN KEY ("image_id") REFERENCES maketing.reference_images ("id")
);

-- =============================================================
--  REFERENCE_IMAGE_KEYWORDS  (다대다)
-- =============================================================
CREATE TABLE maketing.reference_image_keywords (
    "reference_image_id"    BIGINT  NOT NULL,
    "canonical_keyword_id"  BIGINT  NOT NULL,
    CONSTRAINT "PK_REFERENCE_IMAGE_KEYWORDS"
        PRIMARY KEY ("reference_image_id", "canonical_keyword_id"),
    CONSTRAINT "FK_reference_images_TO_reference_image_keywords"
        FOREIGN KEY ("reference_image_id") REFERENCES maketing.reference_images ("id"),
    CONSTRAINT "FK_canonical_keywords_TO_reference_image_keywords"
        FOREIGN KEY ("canonical_keyword_id") REFERENCES maketing.canonical_keywords ("id")
);

-- =============================================================
--  REFERENCE_CAPTION_KEYWORDS  (다대다)
-- =============================================================
CREATE TABLE maketing.reference_caption_keywords (
    "reference_caption_id"  BIGINT  NOT NULL,
    "canonical_keyword_id"  BIGINT  NOT NULL,
    CONSTRAINT "PK_REFERENCE_CAPTION_KEYWORDS"
        PRIMARY KEY ("reference_caption_id", "canonical_keyword_id"),
    CONSTRAINT "FK_reference_captions_TO_reference_caption_keywords"
        FOREIGN KEY ("reference_caption_id") REFERENCES maketing.reference_captions ("id"),
    CONSTRAINT "FK_canonical_keywords_TO_reference_caption_keywords"
        FOREIGN KEY ("canonical_keyword_id") REFERENCES maketing.canonical_keywords ("id")
);