# Case Study Notes Template

## Environment

- Host OS: 
- VM/Docker: 
- App name/version: ATutor 2.2.1
- Web URL: 
- Admin URL: 
- Key ports/services: web, database
- Database: 

## Recon

- Entry points: login, password reset, token validation paths
- Roles/privileges: guest vs authenticated
- Render locations or sinks: authentication logic in PHP

## Vulnerability Hypothesis

- Suspected class: PHP type juggling in comparisons
- Data flow summary: attacker-controlled input -> weak comparison -> auth bypass
- Preconditions: loose equality checks with mixed types

## Chain Outline

- Step 1: locate a weak comparison in auth or token validation
- Step 2: confirm bypass behavior in a safe lab
- Step 3: map any privileged action reachable post-bypass

## Evidence

- Screenshots: access granted without valid credentials
- Logs: request/response showing comparison weakness
- Artifacts: safe proof of privileged access

## Findings

- Root cause: loose comparisons (==) on hashes or tokens
- Fix idea: strict comparisons and constant-time checks
- Open questions: which endpoint is best for a minimal safe demo
