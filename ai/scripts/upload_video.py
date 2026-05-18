from __future__ import annotations

from pathlib import Path

import boto3
from dotenv import load_dotenv
import os


SOURCE_FILE = Path(r"C:\Users\SSAFY\Downloads\test.webm")
S3_OBJECT_KEY = "inputs/c4a8931c-8e80-46f6-acf3-b58351ec8543/test.webm"


def _load_required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return value


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    load_dotenv(env_path)

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source file does not exist: {SOURCE_FILE}")

    access_key = _load_required_env("S3_ACCESS_KEY")
    secret_key = _load_required_env("S3_SECRET_KEY")
    bucket_name = _load_required_env("S3_BUCKET_NAME")
    region = _load_required_env("S3_REGION")
    cloudfront_domain = _load_required_env("CLOUDFRONT_DOMAIN")

    s3_client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    s3_client.upload_file(
        str(SOURCE_FILE),
        bucket_name,
        S3_OBJECT_KEY,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    print(f"Uploaded: {SOURCE_FILE}")
    print(f"S3 key: {S3_OBJECT_KEY}")
    print(f"S3 URI: s3://{bucket_name}/{S3_OBJECT_KEY}")
    print(f"CloudFront URL: https://{cloudfront_domain}/{S3_OBJECT_KEY}")


if __name__ == "__main__":
    main()
