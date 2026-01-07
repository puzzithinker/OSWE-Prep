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

- Entry points: login, password reset, admin-only routes
- Roles/privileges: guest, student, instructor, admin
- Render locations or sinks: file management, module install, configuration pages

## Vulnerability Hypothesis

- Suspected class: auth bypass leading to privileged actions
- Data flow summary: auth flaw -> access admin function -> server-side effect
- Preconditions: reachable admin endpoint or weak token/nonce validation

## Chain Outline

- Step 1: identify the authentication or authorization weakness
- Step 2: confirm access to a privileged action
- Step 3: verify server-side effect from the privileged action

## Evidence

- Screenshots: bypassed access control, privileged page access
- Logs: requests showing missing or weak auth checks
- Artifacts: safe confirmation of server-side effect

## Findings

- Root cause: missing auth check or weak token validation
- Fix idea: enforce auth and role checks on every privileged route
- Open questions: best minimal indicator of privileged action success
