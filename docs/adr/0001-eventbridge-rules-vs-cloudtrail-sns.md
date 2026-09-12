# ADR-0001: EventBridge Pattern Matching vs CloudTrail S3 Bucket Notifications with SNS

**Status:** Accepted  
**Date:** 2026-06-12  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Automated security remediation requires sub-second reaction times when unapproved security group rules (e.g. `0.0.0.0/0:22`), unencrypted S3 buckets, or public EBS snapshots are created. We evaluated ingestion paths for AWS security findings.

## 2. Options Considered
* **Option A: S3 CloudTrail Ingestion + SNS Topic Fanout**
  - *Evaluation:* High latency (10-15 minute CloudTrail S3 delivery delay), high storage cost, complex S3 bucket policy management.
* **Option B: Native Amazon EventBridge Pattern Matching**
  - *Evaluation:* Sub-second event routing directly from AWS API calls and Security Hub findings; fine-grained event filtering JSON patterns eliminate unnecessary Lambda invocations.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (EventBridge Pattern Matching)**.  
**Trade-Off Accepted:** EventBridge rules must be configured per region or routed via global bus peering; cross-account event routing requires explicit EventBridge resource policies.
