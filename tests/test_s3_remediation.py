#!/usr/bin/env python3
"""
Unit tests for S3 remediation handler
"""

from unittest.mock import MagicMock
from src.handlers.s3_remediation import remediate_s3_public_access

def test_remediate_s3_public_access_success():
    mock_s3 = MagicMock()
    mock_s3.put_public_access_block.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

    result = remediate_s3_public_access("test-unprotected-bucket", s3_client=mock_s3)

    assert result["status"] == "REMEDIATED"
    assert result["bucket"] == "test-unprotected-bucket"
    mock_s3.put_public_access_block.assert_called_once_with(
        Bucket="test-unprotected-bucket",
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    )

def test_remediate_s3_empty_bucket_name():
    result = remediate_s3_public_access("")
    assert result["status"] == "FAILED"
