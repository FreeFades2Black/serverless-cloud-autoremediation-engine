#!/usr/bin/env python3
"""
Unit tests for central event dispatcher
"""

from unittest.mock import patch
from src.dispatcher import lambda_handler

@patch("src.dispatcher.remediate_s3_public_access")
def test_dispatcher_routes_s3_event(mock_s3_rem):
    mock_s3_rem.return_value = {"status": "REMEDIATED", "bucket": "audit-bucket"}

    event = {
        "detail": {
            "eventSource": "s3.amazonaws.com",
            "eventName": "PutBucketPolicy",
            "requestParameters": {"bucketName": "audit-bucket"}
        }
    }

    response = lambda_handler(event, None)
    assert response["status"] == "REMEDIATED"
    mock_s3_rem.assert_called_once_with("audit-bucket")

def test_dispatcher_ignores_unrelated_event():
    event = {
        "detail": {
            "eventSource": "dynamodb.amazonaws.com",
            "eventName": "DescribeTable"
        }
    }
    response = lambda_handler(event, None)
    assert response["status"] == "SKIPPED"
