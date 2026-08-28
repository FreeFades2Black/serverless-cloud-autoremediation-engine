#!/usr/bin/env python3
"""
File: src/handlers/ebs_encryption_guard.py
Description: Audits and tags unencrypted EBS volumes for automated encryption migration
Author: William Free Hall (Free) <whall4.wh@gmail.com>
"""

import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger("EBSHandler")
logger.setLevel(logging.INFO)

def remediate_unencrypted_ebs(volume_id: str, ec2_client=None) -> Dict[str, Any]:
    """
    Checks if an EBS volume is encrypted; tags with NonCompliant:Unencrypted tag.
    """
    if not volume_id:
        return {"status": "FAILED", "reason": "No Volume ID provided"}

    if ec2_client is None:
        ec2_client = boto3.client("ec2")

    try:
        response = ec2_client.describe_volumes(VolumeIds=[volume_id])
        volumes = response.get("Volumes", [])
        if not volumes:
            return {"status": "NOT_FOUND", "volume_id": volume_id}

        volume = volumes[0]
        if not volume.get("Encrypted", False):
            logger.warning(f"[!] Unencrypted volume detected: {volume_id}. Tagging for remediation...")
            ec2_client.create_tags(
                Resources=[volume_id],
                Tags=[
                    {"Key": "ComplianceStatus", "Value": "NON_COMPLIANT"},
                    {"Key": "RemediationAction", "Value": "REQUIRE_KMS_SNAPSHOT_MIGRATION"},
                    {"Key": "AutoRemediationEngine", "Value": "Active"}
                ]
            )
            return {
                "status": "TAGGED_NON_COMPLIANT",
                "volume_id": volume_id,
                "encrypted": False,
                "action": "Applied ComplianceStatus tags"
            }

        return {"status": "COMPLIANT", "volume_id": volume_id, "encrypted": True}

    except Exception as e:
        logger.error(f"[ERROR] Failed to audit EBS volume '{volume_id}': {str(e)}")
        raise e
