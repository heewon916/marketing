from __future__ import annotations

import argparse
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

DEFAULT_DOWNLOAD_ROOT = Path(r"C:\Users\SSAFY\Downloads\drafts")


def _load_required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download all draft images for a session from S3."
    )
    parser.add_argument("session_id", help="Session ID used in the draft S3 key.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_DOWNLOAD_ROOT,
        help="Directory where the session draft files will be downloaded.",
    )
    return parser


def _build_s3_client():
    access_key = _load_required_env("S3_ACCESS_KEY")
    secret_key = _load_required_env("S3_SECRET_KEY")
    region = _load_required_env("S3_REGION")

    return boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


def _list_draft_keys(s3_client, bucket_name: str, session_id: str) -> list[str]:
    prefix = f"ai-drafts/{session_id}/"
    paginator = s3_client.get_paginator("list_objects_v2")

    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            if key.endswith("/"):
                continue
            keys.append(key)

    return sorted(keys)


def main() -> None:
    args = _build_parser().parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")

    bucket_name = _load_required_env("S3_BUCKET_NAME")
    cloudfront_domain = _load_required_env("CLOUDFRONT_DOMAIN")
    s3_client = _build_s3_client()

    draft_keys = _list_draft_keys(s3_client, bucket_name, args.session_id)
    if not draft_keys:
        raise FileNotFoundError(
            f"No drafts found for session_id={args.session_id} in bucket {bucket_name}."
        )

    output_dir = args.output_dir / args.session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    for key in draft_keys:
        destination = output_dir / Path(key).name
        s3_client.download_file(bucket_name, key, str(destination))
        print(f"Downloaded: s3://{bucket_name}/{key} -> {destination}")
        print(f"CloudFront URL: https://{cloudfront_domain}/{key}")


if __name__ == "__main__":
    main()
