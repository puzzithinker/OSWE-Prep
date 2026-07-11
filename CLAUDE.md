# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an OSWE (Offensive Security Web Expert) exam preparation repository containing curated learning materials, vulnerability case studies, and exploit development notes. The repository is documentation-only with no executable code, build processes, or automated tests.

## Repository Structure

- `README.md` - Primary index of learning materials, practice labs, HTB writeups, and external resources organized by topic (XXE, Java/PHP/.NET deserialization, SQLi, file upload, etc.)
- `OSWE-Study-Roadmap.md` - 8-week study plan (recommended start)
- `Exam-Day-Runbook.md`, `Progress-Tracker.md`, `Report-Snippet-Templates.md`, `Speed-Drills.md` - Exam ops and practice tracking
- `Lab-Setup-Matrix.md` - Skill → lab/PoC pairing
- `guides/` - Methodology (SQLi, deserial, XSS chains, sinks, decision trees, etc.)
- `drills/`, `study-log/` - Cold-start scenarios and personal session logs
- `OSWE-Prep-content.md` - Consolidated preparation content
- `Building a Reusable OSWE PoC Skeleton.md` - Guide on creating Python PoC scripts using `uv` for project initialization and dependency management
- `Exploit Writing for OSWE.md` - Focused guide on Python exploit development using the `requests` library, including code snippets and best practices
- `Atmail-6.4-XSS-RCE-Study.md` - Specific vulnerability case study
- `AGENTS.md` - Agent-specific guidelines for the repository
- `notes/` - Case study templates and completed vulnerability analyses
  - `CASE-template.md` - Standardized template for documenting new vulnerability case studies
  - Individual case files (e.g., `ATMAIL-6.4.md`, `ATUTOR-2.2.1-*.md`, `BASSMASTER-1.5.1-*.md`, etc.)
- `poc-examples/` - Stage-based PoCs with Notes.md lab manuals

## Common Development Commands

**Verification Commands:**
```bash
# Find placeholders before publishing
rg "TODO|FIXME"

# Verify link formatting
rg "http"
```

No build, test, or deployment commands exist - all changes are plain Markdown edits.

## Working with Case Studies

When creating a new vulnerability case study:
1. Copy `notes/CASE-template.md` to a new file with descriptive naming (e.g., `notes/APP-VERSION-VULN-TYPE.md`)
2. Fill in the template sections: Environment, Recon, Vulnerability Hypothesis, Chain Outline, Evidence, and Findings
3. Link the new case study from `README.md` if it represents a major learning resource

The template follows a structured approach:
- **Environment**: Setup details (OS, VM, app version, URLs, ports, database)
- **Recon**: Entry points, roles/privileges, render locations
- **Vulnerability Hypothesis**: Suspected vulnerability class, data flow, preconditions
- **Chain Outline**: Step-by-step exploitation chain
- **Evidence**: Screenshots, logs, artifacts
- **Findings**: Root cause analysis and potential fixes

## Content Organization Patterns

- Use Markdown tables with `| Order | Name | Link |` format for resource catalogs
- Organize resources by vulnerability type: deserialization (Java/.NET/PHP/Node), SQL injection (MySQL/MSSQL/Postgres), file upload, XXE, XSS, type juggling, etc.
- Keep headings in sentence case
- Use descriptive file names for standalone guides

## Commit Style

Follow the existing git history pattern of short, direct commit messages like "Update README.md". Use more specific messages only when documenting significant content additions or structural changes.

## Security Note

This repository is for authorized security testing, CTF challenges, and educational purposes only. Do not include credentials, lab access tokens, or links to non-public resources.
