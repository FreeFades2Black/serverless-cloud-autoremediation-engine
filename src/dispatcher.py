#!/usr/bin/env python3
"""
File: src/dispatcher.py
Description: Central EventBridge Event Router & Incident Dispatcher
Author: William Free Hall (Free) <whall4.wh@gmail.com>
"""

import json
import logging
from typing import Dict, Any

try:
    from src.handlers.s3_remediation import remediate_s3_public_access
    from src.handlers.security_group_cleaner import remediate_open_security_group
    from src.handlers.ebs_encryption_guard import remediate_unencrypted_ebs
except ImportError:
    from handlers.s3_remediation import remediate_s3_public_access
    from handlers.security_group_cleaner import remediate_open_security_group
    from handlers.ebs_encryption_guard import remediate_unencrypted_ebs

logger = logging.getLogger("IncidentDispatcher")
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main entry point for AWS EventBridge incident notifications.
    Inspects CloudTrail event source and routes to dedicated handler.
    """
    logger.info(f"Received EventBridge Event: {json.dumps(event)}")
    detail = event.get("detail", {})
    event_source = detail.get("eventSource", "")
    event_name = detail.get("eventName", "")

    result = {"status": "SKIPPED", "message": "No remediation required."}

    try:
        if event_source == "s3.amazonaws.com" and event_name in ["PutBucketPolicy", "PutBucketAcl"]:
            bucket_name = detail.get("requestParameters", {}).get("bucketName", "")
            result = remediate_s3_public_access(bucket_name)

        elif event_source == "ec2.amazonaws.com" and event_name == "AuthorizeSecurityGroupIngress":
            sg_id = detail.get("requestParameters", {}).get("groupId", "")
            ip_permissions = detail.get("requestParameters", {}).get("ipPermissions", {})
            result = remediate_open_security_group(sg_id, ip_permissions)

        elif event_source == "ec2.amazonaws.com" and event_name == "CreateVolume":
            volume_id = detail.get("responseElements", {}).get("volumeId", "")
            result = remediate_unencrypted_ebs(volume_id)

    except Exception as e:
        logger.error(f"Failed to execute remediation: {str(e)}", exc_info=True)
        return {"status": "ERROR", "error": str(e)}

    return result

if __name__ == "__main__":
    test_event = {
        "detail": {
            "eventSource": "s3.amazonaws.com",
            "eventName": "PutBucketAcl",
            "requestParameters": {"bucketName": "test-unprotected-bucket"}
        }
    }
    print(lambda_handler(test_event, None))
