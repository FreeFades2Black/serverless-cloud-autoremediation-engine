# Incident Post-Mortem: Recursive EventBridge Remediation Loop on Security Group Rule Revoke

**Incident Date:** 2026-08-04  
**Impact Duration:** 14 minutes  
**Severity:** SEV-2  
**Root Cause:** Security group cleaner Lambda revoked `0.0.0.0/0` ingress rules, generating an `AuthorizeSecurityGroupIngress` / `RevokeSecurityGroupIngress` CloudTrail event that matched the EventBridge rule pattern, triggering a recursive 1,200 invocation storm.

## Timeline
* **16:02 UTC:** Engineer created test security group with open SSH port.
* **16:03 UTC:** Lambda revoked the rule successfully, emitting CloudTrail event.
* **16:04 UTC:** Broad EventBridge pattern captured the revocation event as a new mutation, triggering another Lambda invocation.
* **16:10 UTC:** CloudWatch alarm paged on-call engineer for Lambda concurrent execution spike (120 concurrent executions).
* **16:15 UTC:** Disabled EventBridge rule temporarily.
* **16:18 UTC:** Patched EventBridge pattern with explicit filter excluding user identity `arn:aws:sts::*:assumed-role/AutoremediationEngineRole/*`.

## Corrective Actions
1. Added negative match condition to EventBridge event pattern:
   ```json
   "userIdentity": {
     "sessionContext": {
       "sessionIssuer": {
         "userName": [{"anything-but": "AutoremediationEngineRole"}]
       }
     }
   }
   ```
2. Implemented Lambda reserved concurrency cap of 20 to prevent cloud-wide throttles during loops.
