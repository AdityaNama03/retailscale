"""
upload_to_s3.py

Uploads raw Olist CSVs from data/raw/ to S3 under a date-partitioned
bronze path:

    s3://<bucket>/bronze/<table_name>/ingestion_date=YYYY-MM-DD/<file>.csv

Idempotent: if a file already exists at today's partition, it's skipped
unless --force is passed.

Includes retry with exponential backoff for transient upload failures.
"""

import argparse
import os
import sys
import time
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

FILE_TABLE_MAP = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_customers_dataset.csv": "customers",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "category_translation",
}


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def file_exists_in_s3(s3_client, bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def upload_with_retry(s3_client, local_path, bucket, key, extra_args,
                       max_retries=3, base_delay=2):
    """Upload a file to S3 with exponential backoff retry on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            s3_client.upload_file(
                Filename=str(local_path),
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args,
            )
            return  # success
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if attempt == max_retries:
                raise
            wait = base_delay * (2 ** (attempt - 1))  # 2s, 4s, 8s...
            print(f"  ! Upload failed ({error_code}) for {key}, "
                  f"retry {attempt}/{max_retries} in {wait}s...")
            time.sleep(wait)


def upload_dataset(raw_dir: Path, bucket: str, ingestion_date: str, force: bool = False):
    s3_client = get_s3_client()
    uploaded, skipped, missing, failed = [], [], [], []

    for filename, table_name in FILE_TABLE_MAP.items():
        local_path = raw_dir / filename
        if not local_path.exists():
            missing.append(filename)
            continue

        key = f"bronze/{table_name}/ingestion_date={ingestion_date}/{filename}"

        if not force and file_exists_in_s3(s3_client, bucket, key):
            skipped.append(key)
            continue

        try:
            upload_with_retry(
                s3_client,
                local_path,
                bucket,
                key,
                extra_args={
                    "Metadata": {
                        "source": "olist_dataset",
                        "ingestion_date": ingestion_date,
                    }
                },
            )
            uploaded.append(key)
        except ClientError as e:
            print(f"  ! FAILED after retries: {key} ({e.response['Error']['Code']})")
            failed.append(key)

    return uploaded, skipped, missing, failed


def main():
    parser = argparse.ArgumentParser(description="Upload Olist CSVs to S3 bronze zone")
    parser.add_argument("--raw-dir", default="data/raw", help="Local folder with raw CSVs")
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET", "retailscale-landing"))
    parser.add_argument("--date", default=str(date.today()), help="Ingestion date, YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Re-upload even if file exists")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        print(f"ERROR: {raw_dir} does not exist. Download the dataset first.")
        sys.exit(1)

    uploaded, skipped, missing, failed = upload_dataset(
        raw_dir, args.bucket, args.date, args.force
    )

    print(f"\nIngestion date: {args.date}")
    print(f"Uploaded ({len(uploaded)}):")
    for k in uploaded:
        print(f"  + {k}")
    print(f"Skipped, already present ({len(skipped)}):")
    for k in skipped:
        print(f"  = {k}")
    if missing:
        print(f"Missing local files ({len(missing)}):")
        for f in missing:
            print(f"  ! {f}")
    if failed:
        print(f"Failed after retries ({len(failed)}):")
        for k in failed:
            print(f"  x {k}")
        sys.exit(1)


if __name__ == "__main__":
    main()