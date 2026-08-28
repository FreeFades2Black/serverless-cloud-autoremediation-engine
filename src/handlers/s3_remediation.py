#!/usr/bin/env python3
"""
File: src/handlers/s3_remediation.py
Description: Enforces S3 Public Access Block on non-compliant buckets
Author: William Free Hall (Free) <whall4.wh@gmail.com>
"""

import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger("S3RemediationHandler")
logger.setLevel(logging.INFO)

def remediate_s3_public_access(bucket_name: str, s3_client=None) -> Dict[str, Any]:
    """
    Enforces full Public Access Block on target S3 bucket.
    """
    if not bucket_name:
        return {"status": "FAILED", "reason": "No bucket name provided"}

    if s3_client is None:
        s3_client = boto3.client("s3")

    logger.info(f"[*] Applying strict PublicAccessBlock to S3 bucket: {bucket_name}...")

    try:
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True
            }
        )
        logger.info(f"[SUCCESS] S3 bucket '{bucket_name}' secured against public access.")
        return {
            "status": "REMEDIATED",
            "bucket": bucket_name,
            "action": "PutPublicAccessBlock",
            "enforced_controls": ["BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"]
        }
    except Exception as e:
        logger.error(f"[ERROR] Failed to secure S3 bucket '{bucket_name}': {str(e)}")
        raise e
