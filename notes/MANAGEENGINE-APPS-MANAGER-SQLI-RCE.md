# Case Study Notes Template

## Environment

- Host OS: 
- VM/Docker: 
- App name/version: ManageEngine Applications Manager
- Web URL: 
- Admin URL: 
- Key ports/services: web, database
- Database: 

## Recon

- Entry points: parameters that reach database queries
- Roles/privileges: authenticated vs unauthenticated routes
- Render locations or sinks: SQL query construction paths

## Vulnerability Hypothesis

- Suspected class: SQL injection that can reach a server-side effect
- Data flow summary: request param -> query -> DB feature -> server effect
- Preconditions: injectable parameter and reachable code path

## Chain Outline

- Step 1: confirm injectable parameter (safe tests)
- Step 2: identify DB features that could lead to server effects
- Step 3: verify server-side effect in a safe, lab-only manner

## Evidence

- Screenshots: error or response pattern indicating SQL influence
- Logs: request/response pairs showing query manipulation
- Artifacts: safe confirmation of server-side effect

## Findings

- Root cause: unparameterized query construction
- Fix idea: prepared statements and strict input validation
- Open questions: which DB feature is present in this version
