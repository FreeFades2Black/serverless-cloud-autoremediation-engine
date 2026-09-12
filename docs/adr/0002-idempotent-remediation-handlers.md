# ADR-0002: Idempotent Remediation Handlers with DynamoDB Distributed Leases

**Status:** Accepted  
**Date:** 2026-06-29  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
AWS Security Hub and EventBridge frequently deliver duplicate event payloads during network retries. When a remediation handler strips a public security group ingress rule, duplicate concurrent Lambda executions can trigger AWS API race conditions (`InvalidPermission.NotFound`).

## 2. Options Considered
* **Option A: Stateless In-Memory Deduplication**
  - *Evaluation:* Fails when separate Lambda execution contexts process duplicate events concurrently.
* **Option B: DynamoDB Conditional Write Distributed Locks with 5-Minute TTL**
  - *Evaluation:* Uses a unique event hash (`MD5(resource_id + event_time)`) with a conditional write (`attribute_not_exists(lock_key)`). Guarantees exactly-once remediation execution.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (DynamoDB Distributed Leases)**.  
**Trade-Off Accepted:** Introduces a minimal DynamoDB read/write capacity overhead (~$0.25/mo) in exchange for zero duplicate remediation race conditions.
