# Atmail 6.4 XSS → RCE (CVE-2012-2593) Study Guide

This guide is for learning and note‑taking only. It focuses on concepts, data flow, and verification thinking, not exploit steps or payloads.

## Goal

Understand how a stored or privileged XSS in a webmail admin context can be chained into server‑side execution by abusing trusted actions.

## Core Concepts

- Stored XSS and admin context: why payloads are more powerful when executed in a privileged session.
- Session riding: using a victim’s authenticated browser to perform actions.
- Privilege escalation via UI workflows: identifying “dangerous” admin actions that lead to server‑side effects.
- File handling and upload flows: how misconfigurations can allow server‑side code placement.
- Server‑side command execution: how a web app transitions from “file written” to “code executed.”

## Threat Model Summary

- Attacker can inject content into a place the admin will view (inbox, admin panel, user profile, etc.).
- Admin visits the page; malicious script runs in their session.
- Script performs an authenticated action that the attacker could not do directly.
- Action results in server‑side code execution or persistent server‑side control.

## Study Workflow

1. Identify user‑controlled fields that are rendered in admin‑visible pages.
2. Trace how that content is stored and rendered (DB table, template, sanitizer).
3. Identify admin‑only actions with dangerous side effects (file management, configuration, plugin install).
4. Check whether those actions allow arbitrary content to reach a server‑side execution point.
5. Map the chain: input → storage → admin view → privileged action → server effect.

## Evidence Checklist

- Proof that the injected content is stored and rendered.
- Proof that admin views the content in a privileged session.
- Proof that a privileged action was invoked by the browser.
- Proof that the server performed an unexpected side effect.

## Questions to Answer in Notes

- Where is the first injection point? Which view renders it?
- What escaping/sanitization is applied?
- Which admin action is reachable from the XSS context?
- What server‑side file path or handler is involved?
- What is the minimal evidence that the action succeeded?

## Safe Practice Tips

- Focus on clean recon: map endpoints, roles, and workflows.
- Use a lab copy of the app only; avoid public targets.
- Keep a clear chain diagram in your notes.

## Suggested Note Template

- App version and setup:
- Injection point:
- Storage location:
- Admin view:
- Privileged action:
- Server‑side effect:
- Verification evidence:

## Lab Setup Checklist (Conceptual)

- Confirm the exact Atmail version and dependencies.
- Identify required services (web server, database, mail service).
- Record default ports and admin URL.
- Create two test users: one attacker, one admin.
- Snapshot the environment so you can reset quickly.

## Lab Commands & Ports (Fill In)

- Start/stop commands:
- Web URL:
- Admin URL:
- Mail ports:
- Database port:
- Notes: version string, default creds, and any tweaks.

## PoC Skeleton Stages (Safe Outline)

- Stage 0: Configuration and context (target, proxy, roles).
- Stage 1: Recon (identify entry point and render location).
- Stage 2: Injection confirmation (prove stored render behavior).
- Stage 3: Privileged action mapping (identify admin action path).
- Stage 4: Trigger chain (simulate admin action via session).
- Stage 5: Verification (confirm server‑side effect safely).

## Related Reading

- CVE summary and vendor advisory.
- Public writeups of the vulnerability chain (read for understanding, not copy‑pasting).

## Next Steps

- Draft a local PoC outline using your skeleton: stages only (recon → confirm → chain → verify).
- Add only safe placeholders in code until you can validate each stage in your lab.
