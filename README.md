# lark-skills

This repository is a skills source repository that can be installed directly via `npx skills add`.

## Purpose

- Source repo: `Piasy/lark-skills`
- Goal: install skills directly through the skills CLI
- Users do not need to manually clone this repository before installation

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

## Trigger Prompt Example

When asking an agent to run this workflow, explicitly name the skill `markdown-larkdoc-sync` in your prompt.
This avoids accidental routing to other installed `lark-*` skills that also call `lark-cli`.

Example prompt:

```text
Please use the markdown-larkdoc-sync skill to sync docs/weekly.md with its bound Lark doc.
```

## License

This repository is released under the MIT License.
