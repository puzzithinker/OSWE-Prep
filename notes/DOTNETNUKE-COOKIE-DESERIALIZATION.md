# Case Study Notes Template

## Environment

- Host OS: 
- VM/Docker: 
- App name/version: DotNetNuke (<9.1.1)
- Web URL: 
- Admin URL: 
- Key ports/services: web, .NET runtime
- Database: 

## Recon

- Entry points: cookies or headers that carry serialized data
- Roles/privileges: anonymous vs authenticated cookies
- Render locations or sinks: deserialization handlers

## Vulnerability Hypothesis

- Suspected class: insecure deserialization via cookies
- Data flow summary: cookie -> deserializer -> object graph -> side effect
- Preconditions: gadget availability and unsafe deserialization

## Chain Outline

- Step 1: locate cookie or header deserialization
- Step 2: confirm unsafe deserialization behavior in a safe lab
- Step 3: verify a controlled server-side effect

## Evidence

- Screenshots: responses showing deserialization influence
- Logs: request/response pairs with cookie variations
- Artifacts: safe confirmation of server-side effect

## Findings

- Root cause: deserialization of untrusted data
- Fix idea: avoid unsafe deserialization or enforce strict validation
- Open questions: which gadget chains are present in this version
