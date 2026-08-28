#!/usr/bin/env python3
"""
Unit tests for Security Group cleaner handler
"""

from unittest.mock import MagicMock
from src.handlers.security_group_cleaner import remediate_open_security_group

def test_remediate_open_security_group_revokes_ssh():
    mock_ec2 = MagicMock()
    mock_ec2.revoke_security_group_ingress.return_value = {"Return": True}

    ip_permissions = [
        {
            "fromPort": 22,
            "toPort": 22,
            "ipRanges": {"items": [{"cidrIp": "0.0.0.0/0"}]}
        },
        {
            "fromPort": 443,
            "toPort": 443,
            "ipRanges": {"items": [{"cidrIp": "0.0.0.0/0"}]}
        }
    ]

    result = remediate_open_security_group("sg-12345678", ip_permissions, ec2_client=mock_ec2)

    assert result["status"] == "REMEDIATED"
    assert result["revoked_count"] == 1
    mock_ec2.revoke_security_group_ingress.assert_called_once()

def test_compliant_security_group():
    mock_ec2 = MagicMock()
    ip_permissions = [
        {
            "fromPort": 443,
            "toPort": 443,
            "ipRanges": {"items": [{"cidrIp": "0.0.0.0/0"}]}
        }
    ]
    result = remediate_open_security_group("sg-12345678", ip_permissions, ec2_client=mock_ec2)
    assert result["status"] == "COMPLIANT"
    mock_ec2.revoke_security_group_ingress.assert_not_called()
