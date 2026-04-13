# lark-skills

This repository is a skills source repository that can be installed directly via `npx skills add`.

## Purpose

- Source repo: `Piasy/lark-skills`
- Goal: install skills directly through the skills CLI
- Users do not need to manually clone this repository before installation

## Highlighted Skill Workflow

### `markdown-larkdoc-sync`: from draft to reviewed sync commit

`markdown-larkdoc-sync` is a script-first, auditable workflow for a single Markdown file and its bound Lark doc.  
It is designed to make cross-team review practical:

1. Run the skill once to generate or bootstrap the Lark doc from local Markdown.
2. Let teammates review and comment directly in Lark doc.
3. Run the skill again after review to fetch open comments and remote canonical Markdown.
4. Update local Markdown with review feedback.
5. Write back to Lark doc, verify consistency, resolve all comments, and create a dedicated sync commit.

This gives a closed loop: review in Lark, source-of-truth in Markdown, and traceability in Git.

Important: "automatic" here means script-driven after an explicit agent run, not background continuous sync.

## Diagram Policy

- In Markdown, flow diagrams are authored with Mermaid code fences.
- In Lark doc, the same diagrams are persisted as text-drawing add-ons (`codeChart`).
- The workflow does not use whiteboard blocks for these diagrams.

## What Is Scripted in This Workflow

- Scripted frontmatter binding read/write (no manual parsing or hand edits)
- Doc key resolution and sync-baseline lookup from Git
- Canonical remote Markdown fetch for merge safety
- Open-comment fetching and batch resolution
- Write-back verification (`overwrite`) and Mermaid-to-`codeChart` conversion handling
- Dedicated sync commit creation for auditability

## Install

- Install all skills: `npx skills add Piasy/lark-skills -g -y`
- Install a single skill: `npx skills add Piasy/lark-skills -s markdown-larkdoc-sync -g -y`
- Local install for development: `npx skills add . -g -y`
- List available skills: `npx skills add Piasy/lark-skills -g -y --list`

## Runtime Prerequisites

- `python3 >= 3.11`
- `git`
- `lark-cli`
- authenticated `lark-cli`

## Frontmatter Constraints

For `markdown-larkdoc-sync`, frontmatter is a restricted subset and must be handled via provided scripts.

## Current Skills

- `markdown-larkdoc-sync`: a script-first workflow for manually syncing one Markdown file with one Lark doc, including frontmatter binding read/write, doc key resolution, sync baseline lookup, open-comment fetch/resolve, and sync-commit finalization.

This repository currently contains only the skill above; future additions are defined by discoverable `SKILL.md` files under `skills/`.

## License

This repository is released under the MIT License.
