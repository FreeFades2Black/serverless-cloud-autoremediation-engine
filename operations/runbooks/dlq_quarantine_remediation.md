# Operational Runbook: Triage SQS Dead Letter Queue (DLQ) Remediation Failures

**Severity:** P2 / Security Remediation Blocked  
**Target Systems:** AWS Lambda Dispatcher, SQS Dead Letter Queue, Security Hub

## Diagnostic Workflow

### 1. Check DLQ Approximate Message Count
```bash
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/remediation-dlq \
  --attribute-names ApproximateNumberOfMessages
```

### 2. Receive and Inspect Failed Finding Payload
```bash
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/remediation-dlq \
  --max-number-of-messages 1 \
  --attribute-names All | jq .
```

### 3. Diagnose Common Failure Causes
- `AccessDeniedException`: The Lambda execution role lacks permissions on target resource (e.g. SCP blocking bucket policy modification).
- `InvalidParameterValue`: Target resource was deleted before remediation executed (ephemeral test runner).

### 4. Re-drive Messages After IAM Policy Patch
```bash
aws sqs start-message-move-task \
  --source-arn arn:aws:sqs:us-east-1:123456789012:remediation-dlq \
  --destination-arn arn:aws:sqs:us-east-1:123456789012:remediation-main-queue
```
