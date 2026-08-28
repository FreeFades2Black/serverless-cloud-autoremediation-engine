#!/usr/bin/env python3
"""
File: src/handlers/security_group_cleaner.py
Description: Identifies and revokes 0.0.0.0/0 ingress rules on sensitive ports (22, 3389)
Author: William Free Hall (Free) <whall4.wh@gmail.com>
"""

import boto3
import logging
from typing import Dict, Any, List

logger = logging.getLogger("SGRemediationHandler")
logger.setLevel(logging.INFO)

RESTRICTED_PORTS = [22, 3389, 23]

def remediate_open_security_group(sg_id: str, ip_permissions: Any, ec2_client=None) -> Dict[str, Any]:
    """
    Scans security group ingress permissions and strips any 0.0.0.0/0 rules matching restricted ports.
    """
    if not sg_id:
        return {"status": "FAILED", "reason": "No Security Group ID provided"}

    if ec2_client is None:
        ec2_client = boto3.client("ec2")

    revoked_rules: List[Dict] = []

    try:
        # Inspect rules to identify non-compliant 0.0.0.0/0 entries
        items = ip_permissions.get("items", []) if isinstance(ip_permissions, dict) else ip_permissions
        if not isinstance(items, list):
            items = [ip_permissions]

        for rule in items:
            from_port = rule.get("fromPort") or rule.get("FromPort", 0)
            to_port = rule.get("toPort") or rule.get("ToPort", 0)
            ip_ranges = rule.get("ipRanges", {}).get("items", []) if isinstance(rule.get("ipRanges"), dict) else rule.get("IpRanges", [])

            for ip_range in ip_ranges:
                cidr = ip_range.get("cidrIp") or ip_range.get("CidrIp", "")
                if cidr == "0.0.0.0/0" and any(p >= from_port and p <= to_port for p in RESTRICTED_PORTS):
                    logger.warning(f"[!] Non-compliant rule detected on SG {sg_id}: Port {from_port}-{to_port} open to {cidr}")
                    ec2_client.revoke_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=[rule]
                    )
                    revoked_rules.append(rule)

        return {
            "status": "REMEDIATED" if revoked_rules else "COMPLIANT",
            "security_group_id": sg_id,
            "revoked_count": len(revoked_rules),
            "revoked_rules": revoked_rules
        }

    except Exception as e:
        logger.error(f"[ERROR] Failed to remediate Security Group '{sg_id}': {str(e)}")
        raise e
