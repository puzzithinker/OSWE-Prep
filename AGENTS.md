# Repository Guidelines

## Project Structure & Module Organization

This repository is a curated set of OSWE preparation notes and resource lists written in Markdown.

- `README.md` is the primary index of learning materials, labs, and writeups.
- `OSWE-Prep-content.md` consolidates broader prep content.
- `Building a Reusable OSWE PoC Skeleton.md` and `Exploit Writing for OSWE.md` are focused guides.
- `notes/` contains reusable case study templates; copy `notes/CASE-template.md` when starting a new topic.

Add new topics as standalone Markdown files with descriptive titles, and link them from `README.md`.

## Build, Test, and Development Commands

There are no build or test commands. Changes are plain Markdown edits.

Useful checks:

- `rg "TODO|FIXME"` to find placeholders before publishing.
- `rg "http"` to spot new links and verify formatting.

## Coding Style & Naming Conventions

- Use Markdown headings (`#`, `##`) for structure; keep headings short.
- Prefer bullet lists and tables for resource catalogs.
- Use sentence case for section titles and list entries.
- File naming follows descriptive titles, e.g. `Exploit Writing for OSWE.md`.

## Testing Guidelines

No automated tests exist. Manually verify:

- Links are valid and placed in the correct section.
- Tables align with the existing `|` column format.
- New files are referenced in `README.md`.

## Commit & Pull Request Guidelines

Git history uses short, direct messages like `Update README.md`. Follow that style unless a more specific change is needed.

Pull requests should include:

- A brief description of added/updated resources.
- Source links for new materials.
- Any notes about scope changes (new section, renamed file, etc.).

## Security & Configuration Tips

Do not include sensitive credentials or lab access tokens. Link to public resources only.

## Agent-Specific Instructions

If you add new guidelines, keep this file between 200–400 words and aligned with the repository’s documentation-only nature.
