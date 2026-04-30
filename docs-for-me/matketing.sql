CREATE TABLE `reference_captions` (
	`id`	BIGINT	NOT NULL,
	`canonical_keyword_id`	UUID	NOT NULL,
	`caption_content`	TEXT	NOT NULL,
	`embedding`	VECTOR(1536)	NOT NULL
);

CREATE TABLE `upload_history` (
	`id`	UUID	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`uploaded_at`	TIMESTAMPTZ	NOT NULL,
	`uploaded_date`	DATE	NULL,
	`day_of_week`	SMALLINT	NOT NULL,
	`created_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `canonical_keywords` (
	`id`	UUID	NOT NULL,
	`code`	VARCHAR(100)	NULL,
	`display_name`	VARCHAR(200)	NOT NULL	COMMENT '사용자/운영자',
	`embedding`	VECTOR(1536)	NOT NULL	COMMENT '표준',
	`created_at`	TIMESTAMPTZ	NOT NULL
);

CREATE TABLE `reference_images` (
	`id`	BIGINT	NOT NULL,
	`canonical_keyword_id`	UUID	NOT NULL,
	`s3_key`	VARCHAR(200)	NOT NULL,
	`focus_subject`	VARCHAR(100)	NULL,
	`shot_type`	VARCHAR(50)	NULL	COMMENT '예:',
	`camera_angle`	VARCHAR(50)	NULL	COMMENT '예:',
	`lighting`	VARCHAR(50)	NULL	COMMENT '예:',
	`style_filter`	VARCHAR(100)	NULL	COMMENT '예:'
);

CREATE TABLE `account_weekly_metrics` (
	`id`	UUID	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`total_reach`	INTEGER	NULL,
	`target_post_count`	INTEGER	NULL,
	`actual_post_count`	INTEGER	NULL,
	`achievement_rate`	DECIMAL(5, 2)	NULL,
	`visit_intent_score`	INTEGER	NULL,
	`created_at`	TIMESTAMPTZ	NULL,
	`is_deleted`	BOOLEAN	NULL
);

CREATE TABLE `users` (
	`id`	UUID	NOT NULL,
	`instagram_user_id`	VARCHAR(100)	NOT NULL,
	`instagram_username`	VARCHAR(100)	NULL,
	`access_token`	TEXT	NULL,
	`token_expires_at`	TIMESTAMPTZ	NULL,
	`refresh_token`	TEXT	NULL,
	`camera_mic_granted`	BOOLEAN	NULL,
	`created_at`	TIMESTAMPTZ	NULL,
	`updated_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `store_hours` (
	`store_id`	UUID	NOT NULL,
	`monday_open`	TIME	NULL,
	`tuesday_open`	TIME	NULL,
	`wednesday_open`	TIME	NULL,
	`thursday_open`	TIME	NULL,
	`friday_open`	TIME	NULL,
	`saturday_open`	TIME	NULL,
	`sunday_open`	TIME	NULL,
	`monday_close`	TIME	NULL,
	`tuesday_close`	TIME	NULL,
	`wednesday_close`	TIME	NULL,
	`thursday_close`	TIME	NULL,
	`friday_close`	TIME	NULL,
	`saturday_close`	TIME	NULL,
	`sunday_close`	TIME	NULL
);

CREATE TABLE `upload_patterns` (
	`id`	UUID	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`day_of_week`	SMALLINT	NOT NULL,
	`predicted_time`	TIME	NULL,
	`sample_count`	INTEGER	NULL,
	`last_updated`	TIMESTAMPTZ	NULL
);

CREATE TABLE `api_token_logs` (
	`id`	UUID	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`old_expires_at`	TIMESTAMPTZ	NULL,
	`new_expires_at`	TIMESTAMPTZ	NULL,
	`created_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `contents` (
	`id`	BIGINT	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`session_id`	UUID	NULL,
	`caption`	TEXT	NULL,
	`instagram_media_id`	VARCHAR(100)	NULL,
	`instagram_permalink`	TEXT	NULL,
	`published_at`	TIMESTAMPTZ	NULL,
	`is_deleted`	BOOLEAN	NULL,
	`deleted_at`	TIMESTAMPTZ	NULL,
	`created_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `notifications` (
	`id`	UUID	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`notification`	TEXT	NULL,
	`scheduled_at`	TIMESTAMPTZ	NULL,
	`created_at`	TIMESTAMPTZ	NULL,
	`type`	SMALLINT	NULL,
	`status`	SMALLINT	NULL,
	`sent_at`	TIMESTAMPTZ	NULL,
	`updated_at`	TIMESTAMPTZ	NULL,
	`retry_count`	INTEGER	NULL,
	`failure_reason`	TEXT	NULL,
	`web_url`	TEXT	NULL,
	`reference_id`	UUID	NULL
);

CREATE TABLE `contents_images` (
	`id`	UUID	NOT NULL,
	`contents_id`	BIGINT	NOT NULL,
	`s3_key`	VARCHAR(200)	NOT NULL
);

CREATE TABLE `device_tokens` (
	`id`	UUID	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`token`	TEXT	NULL,
	`platform`	VARCHAR	NULL,
	`is_active`	BOOLEAN	NULL,
	`created_at`	TIMESTAMPTZ	NULL,
	`updated_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `menus` (
	`id`	UUID	NOT NULL,
	`store_id`	UUID	NOT NULL,
	`name`	VARCHAR(200)	NOT NULL,
	`price`	INTEGER	NULL,
	`description`	TEXT	NULL,
	`weather_tags`	JSONB	NULL	DEFAULT '',
	`holiday_tags`	JSONB	NULL	DEFAULT '',
	`created_at`	TIMESTAMPTZ	NULL,
	`updated_at`	TIMESTAMPTZ	NULL,
	`embedding`	vector(1536)	NULL
);

CREATE TABLE `video_recordings` (
	`id`	UUID	NOT NULL,
	`contents_id`	BIGINT	NOT NULL,
	`s3_key`	VARCHAR(200)	NOT NULL
);

CREATE TABLE `instagram_metrics` (
	`id`	UUID	NOT NULL,
	`contents_id`	BIGINT	NULL,
	`store_id`	UUID	NOT NULL,
	`instagram_media_id`	VARCHAR(100)	NOT NULL,
	`reaches`	INTEGER	NULL,
	`saves`	INTEGER	NULL,
	`shares`	INTEGER	NULL,
	`likes`	INTEGER	NULL,
	`created_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `holidays` (
	`id`	UUID	NOT NULL,
	`holiday_date`	DATE	NOT NULL,
	`name`	VARCHAR(200)	NOT NULL,
	`created_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `stores` (
	`id`	UUID	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`merchant_id`	VARCHAR(20)	NULL,
	`store_name`	VARCHAR(200)	NOT NULL,
	`category`	category_type	NULL,
	`owner_persona`	owner_persona_type	NULL,
	`address`	TEXT	NULL,
	`latitude`	DECIMAL(10, 7)	NULL,
	`longitude`	DECIMAL(10, 7)	NULL,
	`operating_hours`	JSONB	NULL	COMMENT '영업시간??',
	`created_at`	TIMESTAMPTZ	NULL,
	`updated_at`	TIMESTAMPTZ	NULL
);

CREATE TABLE `reference` (
	`id`	BIGINT	NOT NULL,
	`caption_id`	UUID	NOT NULL,
	`image_id`	UUID	NOT NULL,
	`owner_persona`	owner_persona_type	NULL,
	`store_name`	VARCHAR(200)	NULL,
	`created_at`	DATE	NULL
);

ALTER TABLE `reference_captions` ADD CONSTRAINT `PK_REFERENCE_CAPTIONS` PRIMARY KEY (
	`id`
);

ALTER TABLE `upload_history` ADD CONSTRAINT `PK_UPLOAD_HISTORY` PRIMARY KEY (
	`id`
);

ALTER TABLE `canonical_keywords` ADD CONSTRAINT `PK_CANONICAL_KEYWORDS` PRIMARY KEY (
	`id`
);

ALTER TABLE `reference_images` ADD CONSTRAINT `PK_REFERENCE_IMAGES` PRIMARY KEY (
	`id`
);

ALTER TABLE `account_weekly_metrics` ADD CONSTRAINT `PK_ACCOUNT_WEEKLY_METRICS` PRIMARY KEY (
	`id`
);

ALTER TABLE `users` ADD CONSTRAINT `PK_USERS` PRIMARY KEY (
	`id`
);

ALTER TABLE `store_hours` ADD CONSTRAINT `PK_STORE_HOURS` PRIMARY KEY (
	`store_id`
);

ALTER TABLE `upload_patterns` ADD CONSTRAINT `PK_UPLOAD_PATTERNS` PRIMARY KEY (
	`id`
);

ALTER TABLE `api_token_logs` ADD CONSTRAINT `PK_API_TOKEN_LOGS` PRIMARY KEY (
	`id`
);

ALTER TABLE `contents` ADD CONSTRAINT `PK_CONTENTS` PRIMARY KEY (
	`id`
);

ALTER TABLE `notifications` ADD CONSTRAINT `PK_NOTIFICATIONS` PRIMARY KEY (
	`id`
);

ALTER TABLE `contents_images` ADD CONSTRAINT `PK_CONTENTS_IMAGES` PRIMARY KEY (
	`id`
);

ALTER TABLE `device_tokens` ADD CONSTRAINT `PK_DEVICE_TOKENS` PRIMARY KEY (
	`id`
);

ALTER TABLE `menus` ADD CONSTRAINT `PK_MENUS` PRIMARY KEY (
	`id`
);

ALTER TABLE `video_recordings` ADD CONSTRAINT `PK_VIDEO_RECORDINGS` PRIMARY KEY (
	`id`
);

ALTER TABLE `instagram_metrics` ADD CONSTRAINT `PK_INSTAGRAM_METRICS` PRIMARY KEY (
	`id`
);

ALTER TABLE `holidays` ADD CONSTRAINT `PK_HOLIDAYS` PRIMARY KEY (
	`id`
);

ALTER TABLE `stores` ADD CONSTRAINT `PK_STORES` PRIMARY KEY (
	`id`
);

ALTER TABLE `reference` ADD CONSTRAINT `PK_REFERENCE` PRIMARY KEY (
	`id`
);

ALTER TABLE `store_hours` ADD CONSTRAINT `FK_stores_TO_store_hours_1` FOREIGN KEY (
	`store_id`
)
REFERENCES `stores` (
	`id`
);

