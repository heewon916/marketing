from __future__ import annotations

import boto3

from app.core.config import settings


def build_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


def normalize_s3_key(value: str) -> str:
    return value.lstrip("/")
