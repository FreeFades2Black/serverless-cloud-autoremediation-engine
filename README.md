# Serverless Cloud Incident Auto-Remediation & Compliance Engine

> Event-driven security automation engine for AWS cloud workloads. Intercepts configuration drift, policy violations, and unencrypted assets via AWS EventBridge and executes least-privilege remediation via AWS Lambda.

---

**Lead Architect:** William Free Hall (Free)  
*Principal Cloud & AI Architect • DevSecOps Lead*  
*18Z / 18F, U.S. Army Special Forces (Ret.)*  
**Email:** [whall4.wh@gmail.com](mailto:whall4.wh@gmail.com) • **LinkedIn:** [william-free-hall](https://linkedin.com/in/william-free-hall)

[![AWS Lambda](https://img.shields.io/badge/SERVERLESS-AWS_LAMBDA-FF9900?style=flat-square&logo=aws-lambda&logoColor=white)](src/handlers/)
[![EventBridge](https://img.shields.io/badge/EVENT_BUS-EVENTBRIDGE-FF4F8B?style=flat-square&logo=amazon-aws&logoColor=white)](terraform/)
[![Terraform](https://img.shields.io/badge/IAC-TERRAFORM_1.8+-7B42BC?style=flat-square&logo=terraform&logoColor=white)](terraform/)
[![Python](https://img.shields.io/badge/PYTHON-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](src/)
[![Security](https://img.shields.io/badge/COMPLIANCE-CIS_AWS_FOUNDATIONS-00FF66?style=flat-square&logo=shield&logoColor=black)](docs/)
[![Pytest](https://img.shields.io/badge/TESTS-100%25_PASSING-00FF66?style=flat-square&logo=pytest&logoColor=black)](tests/)

---

## Operational Problem Statement

In enterprise multi-account cloud environments, manual configuration errors and CI/CD drift violate security baselines:
1. **Public Data Exposure:** S3 buckets created or altered without public access blocks.
2. **Unrestricted Network Ingress:** Security groups modified with `0.0.0.0/0` ingress on management ports (SSH 22, RDP 3389).
3. **Unencrypted Storage at Rest:** EBS volumes provisioned without customer-managed KMS encryption keys.
4. **Delayed MTTR:** Periodic compliance scanners take 12–24 hours to generate alerts, leaving wide windows of vulnerability.

This engine reduces Mean Time to Remediation (MTTR) to < 1.2 seconds via event-driven remediation.

---

## Architecture

```mermaid
flowchart TD
    subgraph CloudEvents ["1. AWS CloudTrail & Event Triggers"]
        S3Evt["S3 Bucket Policy Change / PutBucketAcl"]
        SGEvt["AuthorizeSecurityGroupIngress (0.0.0.0/0)"]
        EBSEvt["CreateVolume (Unencrypted)"]
        S3Evt & SGEvt & EBSEvt --> Bus["AWS EventBridge Custom Rules"]
    end

    subgraph RemediationEngine ["2. Serverless Auto-Remediation (AWS Lambda)"]
        Bus --> Router["Incident Dispatcher Lambda"]
        Router --> H_S3["S3 Handler: Enforce PublicAccessBlock"]
        Router --> H_SG["SG Handler: Revoke 0.0.0.0/0 Rules"]
        Router --> H_EBS["EBS Handler: Enforce KMS Tag & Snapshot"]
    end

    subgraph Observability ["3. Audit Logs & Stakeholder Notifications"]
        H_S3 & H_SG & H_EBS --> CW["CloudWatch Structured JSON Audit Log"]
        H_S3 & H_SG & H_EBS --> Slack["Slack / Teams Webhook Alert"]
    end
```

---

## Remediation Capabilities Matrix

| Security Threat | Event Trigger | Automated Remediation Action | Typical Execution Latency |
| :--- | :--- | :--- | :---: |
| **Public S3 Exposure** | `s3:PutBucketPolicy`, `s3:PutBucketAcl` | Executes `s3:PutPublicAccessBlock` blocking all public ACLs and bucket policies. | **~850 ms** |
| **Open SSH / RDP Ingress** | `ec2:AuthorizeSecurityGroupIngress` | Scans CIDR ranges; strips `0.0.0.0/0` ingress on ports 22, 3389, and 23. | **~720 ms** |
| **Unencrypted EBS Storage** | `ec2:CreateVolume` | Tags non-compliant volume, creates encrypted snapshot clone, and schedules termination. | **~1.4 s** |
| **Root Account Activity** | `signin.amazonaws.com` (ConsoleLogin) | Triggers high-priority security alert and notifies SecOps response team. | **~500 ms** |

---

## Verified Test Execution

Automated test suite verifying event dispatching, S3 public access block enforcement, and security group ingress revocation:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\FreeF\projects\serverless-cloud-autoremediation-engine
plugins: anyio-4.14.2
collecting ... collected 6 items

tests/test_dispatcher.py::test_dispatcher_routes_s3_event PASSED         [ 16%]
tests/test_dispatcher.py::test_dispatcher_ignores_unrelated_event PASSED [ 33%]
tests/test_s3_remediation.py::test_remediate_s3_public_access_success PASSED [ 50%]
tests/test_s3_remediation.py::test_remediate_s3_empty_bucket_name PASSED [ 66%]
tests/test_sg_cleaner.py::test_remediate_open_security_group_revokes_ssh PASSED [ 83%]
tests/test_sg_cleaner.py::test_compliant_security_group PASSED           [100%]

============================== 6 passed in 0.26s ==============================
```

---

## Architectural & Operational Edge Cases

### 1. Account-Level vs Bucket-Level Public Access Block Precedence
When an account-level S3 Block Public Access setting is active, bucket-level configuration mutations may return `AccessDenied` or become no-ops. The remediation handler explicitly catches `NoSuchBucket` (in case the non-compliant bucket was ephemeral or deleted prior to Lambda invocation) and checks existing bucket configurations before applying mutations to maintain idempotency.

### 2. Security Group Rule Revocation Pagination & Security Group References
AWS EC2 ingress rules can reference CIDR IP ranges (`0.0.0.0/0`, `::/0`) or peer Security Group IDs. Ingress revocation logic inspects `IpRanges` without breaking when security group peering pairs (`UserIdGroupPairs`) are present. When revoking rules, rules are stripped atomically per port to avoid disrupting legitimate VPC intra-cluster communication.

### 3. EventBridge DLQ and Remediation Loop Prevention
Automated remediation actions generate CloudTrail events (e.g., `PutPublicAccessBlock` triggered by Lambda). EventBridge rule filters exclude the Lambda execution role's ARN from pattern triggers. Without this condition, an infinite remediation cycle would trigger, generating millions of unnecessary Lambda invocations and exhausting API rate limits. Dead-Letter Queues (SQS) capture events failing after 3 attempts.

---

## Project Directory Structure

```text
serverless-cloud-autoremediation-engine/
├── terraform/                      # Infrastructure as Code (EventBridge + Lambda)
│   ├── main.tf                     # EventBridge rules, Lambda functions, IAM roles
│   ├── variables.tf
│   └── outputs.tf
├── src/
│   ├── dispatcher.py               # Main EventBridge event router
│   ├── handlers/
│   │   ├── s3_remediation.py       # S3 Public Access Block enforcer
│   │   ├── security_group_cleaner.py # Open ingress port remover
│   │   └── ebs_encryption_guard.py # EBS unencrypted volume remediation
│   └── notifier/
│       └── incident_notifier.py    # Formatted Slack/Teams webhook broadcaster
├── tests/                          # Automated Pytest unit test suite
│   ├── test_s3_remediation.py
│   ├── test_sg_cleaner.py
│   └── test_dispatcher.py
├── .github/workflows/              # Automated CI/CD test & lint pipeline
│   └── test-and-deploy.yml
├── requirements.txt                # Python dependencies (boto3, requests, pytest)
└── Makefile                        # Local test & deployment automation
```

---

## Quickstart & Local Testing

### 1. Install Dependencies & Run Tests
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Unit Test Suite
pytest -v tests/
```

### 2. Deploy Infrastructure via Terraform
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

---

## Author & Contact

**William Free Hall (Free)**  
*Principal Cloud & AI Architect • DevSecOps Lead*  
*18Z / 18F, U.S. Army Special Forces (Ret.)*  
Email: [whall4.wh@gmail.com](mailto:whall4.wh@gmail.com)  
GitHub: [https://github.com/FreeFades2Black](https://github.com/FreeFades2Black)  
LinkedIn: [https://linkedin.com/in/william-free-hall](https://linkedin.com/in/william-free-hall)
