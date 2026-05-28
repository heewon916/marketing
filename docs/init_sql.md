# 붙여넣은 텍스트 (1).txt

```sql
CREATE TABLE "reference_images" (
	"id"	BIGINT		NOT NULL,
	"sort_order"	SMALLINT		NULL,
	"s3_key"	VARCHAR(200)		NOT NULL,
	"focus_subject"	VARCHAR(100)		NULL,
	"focus_subject_embedding"	VECTOR(1536)		NULL,
	"shot_type"	VARCHAR(20)		NULL,
	"shot_type_code"	VARCHAR(50)		NULL,
	"shot_type_embedding"	VECTOR(1536)		NULL,
	"camera_angle"	VARCHAR(20)		NULL,
	"camera_angle_code"	VARCHAR(50)		NULL,
	"camera_angle_embedding"	VECTOR(1536)		NULL,
	"style_filter"	VARCHAR(100)		NULL,
	"lighting_params"	JSONB		NULL
);

COMMENT ON COLUMN "reference_images"."shot_type" IS '원본';

COMMENT ON COLUMN "reference_images"."camera_angle" IS '원본';

COMMENT ON COLUMN "reference_images"."style_filter" IS '예:';

COMMENT ON COLUMN "reference_images"."lighting_params" IS '표준';

CREATE TABLE "upload_history" (
	"id"	UUID		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"uploaded_at"	TIMESTAMPTZ		NOT NULL,
	"uploaded_date"	DATE		NULL,
	"day_of_week"	SMALLINT		NOT NULL,
	"created_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "account_weekly_metrics" (
	"id"	UUID		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"total_reach"	INTEGER		NULL,
	"target_post_count"	INTEGER		NULL,
	"actual_post_count"	INTEGER		NULL,
	"achievement_rate"	DECIMAL(5, 2)		NULL,
	"visit_intent_score"	INTEGER		NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"is_deleted"	BOOLEAN		NULL
);

CREATE TABLE "users" (
	"id"	UUID		NOT NULL,
	"instagram_user_id"	VARCHAR(100)		NOT NULL,
	"instagram_username"	VARCHAR(100)		NULL,
	"access_token"	TEXT		NULL,
	"token_expires_at"	TIMESTAMPTZ		NULL,
	"camera_mic_granted"	BOOLEAN		NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"updated_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "store_hours" (
	"store_id"	UUID		NOT NULL,
	"monday_open"	TIME		NULL,
	"tuesday_open"	TIME		NULL,
	"wednesday_open"	TIME		NULL,
	"thursday_open"	TIME		NULL,
	"friday_open"	TIME		NULL,
	"saturday_open"	TIME		NULL,
	"sunday_open"	TIME		NULL,
	"monday_close"	TIME		NULL,
	"tuesday_close"	TIME		NULL,
	"wednesday_close"	TIME		NULL,
	"thursday_close"	TIME		NULL,
	"friday_close"	TIME		NULL,
	"saturday_close"	TIME		NULL,
	"sunday_close"	TIME		NULL
);

CREATE TABLE "upload_patterns" (
	"id"	UUID		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"day_of_week"	SMALLINT		NOT NULL,
	"predicted_time"	TIME		NULL,
	"sample_count"	INTEGER		NULL,
	"last_updated"	TIMESTAMPTZ		NULL
);

CREATE TABLE "api_token_logs" (
	"id"	UUID		NOT NULL,
	"user_id"	UUID		NOT NULL,
	"old_expires_at"	TIMESTAMPTZ		NULL,
	"new_expires_at"	TIMESTAMPTZ		NULL,
	"created_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "canonical_keywords" (
	"id"	BIGINT		NOT NULL,
	"code"	VARCHAR(100)		NULL,
	"display_name"	VARCHAR(200)		NOT NULL,
	"embedding"	VECTOR(1536)		NOT NULL,
	"created_at"	TIMESTAMPTZ		NOT NULL
);

COMMENT ON COLUMN "canonical_keywords"."display_name" IS '사용자/운영자가';

COMMENT ON COLUMN "canonical_keywords"."embedding" IS '표준';

CREATE TABLE "reference_captions" (
	"id"	BIGINT		NOT NULL,
	"caption_content"	TEXT		NOT NULL,
	"embedding"	VECTOR(1536)		NOT NULL
);

CREATE TABLE "reference_image_keywords" (
	"reference_image_id"	BIGINT		NOT NULL,
	"canonical_keyword_id"	BIGINT		NOT NULL
);

CREATE TABLE "contents" (
	"id"	BIGINT		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"session_id"	UUID		NULL,
	"caption"	TEXT		NULL,
	"instagram_media_id"	VARCHAR(100)		NULL,
	"instagram_permalink"	TEXT		NULL,
	"published_at"	TIMESTAMPTZ		NULL,
	"is_deleted"	BOOLEAN		NULL,
	"deleted_at"	TIMESTAMPTZ		NULL,
	"created_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "notifications" (
	"id"	UUID		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"notification"	TEXT		NULL,
	"scheduled_at"	TIMESTAMPTZ		NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"type"	SMALLINT		NULL,
	"status"	SMALLINT		NULL,
	"sent_at"	TIMESTAMPTZ		NULL,
	"updated_at"	TIMESTAMPTZ		NULL,
	"retry_count"	INTEGER		NULL,
	"failure_reason"	TEXT		NULL,
	"web_url"	TEXT		NULL,
	"reference_id"	UUID		NULL
);

CREATE TABLE "contents_images" (
	"id"	UUID		NOT NULL,
	"contents_id"	BIGINT		NOT NULL,
	"s3_key"	VARCHAR(200)		NOT NULL
);

CREATE TABLE "device_tokens" (
	"id"	UUID		NOT NULL,
	"user_id"	UUID		NOT NULL,
	"token"	TEXT		NULL,
	"platform"	VARCHAR		NULL,
	"is_active"	BOOLEAN		NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"updated_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "menus" (
	"id"	UUID		NOT NULL,
	"store_id"	UUID		NOT NULL,
	"name"	VARCHAR(200)		NOT NULL,
	"price"	INTEGER		NULL,
	"description"	TEXT		NULL,
	"weather_tags"	JSONB	DEFAULT ''	NULL,
	"holiday_tags"	JSONB	DEFAULT ''	NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"updated_at"	TIMESTAMPTZ		NULL,
	"embedding"	vector(1536)		NULL
);

CREATE TABLE "reference" (
	"id"	BIGINT		NOT NULL,
	"caption_id"	BIGINT		NOT NULL,
	"image_id"	BIGINT		NOT NULL,
	"owner_persona"	maketing.owner_persona_type		NULL,
	"store_name"	VARCHAR(200)		NULL,
	"created_at"	DATE		NULL,
	"instagram_id"	VARCHAR(200)		NULL
);

CREATE TABLE "video_recordings" (
	"id"	UUID		NOT NULL,
	"contents_id"	BIGINT		NOT NULL,
	"s3_key"	VARCHAR(200)		NOT NULL
);

CREATE TABLE "instagram_metrics" (
	"id"	UUID		NOT NULL,
	"contents_id"	BIGINT		NULL,
	"store_id"	UUID		NOT NULL,
	"instagram_media_id"	VARCHAR(100)		NOT NULL,
	"reaches"	INTEGER		NULL,
	"saves"	INTEGER		NULL,
	"shares"	INTEGER		NULL,
	"likes"	INTEGER		NULL,
	"created_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "holidays" (
	"id"	UUID		NOT NULL,
	"holiday_date"	DATE		NOT NULL,
	"name"	VARCHAR(200)		NOT NULL,
	"created_at"	TIMESTAMPTZ		NULL
);

CREATE TABLE "stores" (
	"id"	UUID		NOT NULL,
	"user_id"	UUID		NOT NULL,
	"merchant_id"	VARCHAR(20)		NULL,
	"store_name"	VARCHAR(200)		NOT NULL,
	"category"	category_type		NULL,
	"owner_persona"	owner_persona_type		NULL,
	"address"	TEXT		NULL,
	"latitude"	DECIMAL(10, 7)		NULL,
	"longitude"	DECIMAL(10, 7)		NULL,
	"operating_hours"	JSONB		NULL,
	"created_at"	TIMESTAMPTZ		NULL,
	"updated_at"	TIMESTAMPTZ		NULL
);

COMMENT ON COLUMN "stores"."operating_hours" IS '영업시간??';

CREATE TABLE "reference_caption_keywords" (
	"reference_caption_id"	BIGINT		NOT NULL,
	"canonical_keyword_id"	BIGINT		NOT NULL
);


```
