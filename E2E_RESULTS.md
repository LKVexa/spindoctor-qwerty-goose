# E2E results - spindoctor-qwerty-goose 1.1.0

Host: **real goose CLI 1.54.0** (official release binary from github.com/aaif-goose/goose, Linux x64) with a throwaway HOME, config
and data folders and no account. Model turns come from `tests/stub_llm.py`, a local scripted stand-in for an OpenAI-compatible endpoint
on 127.0.0.1 (`GOOSE_PROVIDER=openai`, `OPENAI_HOST`, placeholder key), so tool calls are scripted; everything between the model and
the engine (plugin install, skill discovery and `load_skill`, recipe rendering, extension startup from the recipe and from config.yaml,
tool naming, the developer shell tool) is the real goose. Python 3.13.5.

Not tested: a real model choosing the tools by itself, goose Desktop and deeplinks, interactive approval prompts, Windows, macOS.

## Host check: 17/17

| Result | Check |
|---|---|
| PASS | plugin.json (Open Plugins manifest): name spindoctor-qwerty, version 1.1.0, description, license GPL-3.0-or-later, author |
| PASS | skill skills/spindoctor-qwerty/SKILL.md: front matter (name, description, license) + honest limits; no hooks (nothing runs on its own) |
| PASS | recipes: stdio extension spindoctor-qwerty = {{ python }} (default python3) + {{ recipe_dir }}/../skills/.../spindoctor_mcp.py, 600 s; task recipe adds prompt {{ task }}; honest limits |
| PASS | tools/goose_setup.py: config.yaml entry with this copy's absolute engine path, deeplink (cmd/arg/id/name/timeout) round-trips, --python py for Windows |
| PASS | MCP server starts (initialize answered, server spindoctor-qwerty 1.1.0) |
| PASS | real goose 1.54.0 (no account): plugin install <git repo> -> open-plugins plugin 1.1.0 in ~/.agents/plugins/spindoctor-qwerty, skill spindoctor-qwerty:spindoctor-qwerty |
| PASS | real goose: skills list shows spindoctor-qwerty:spindoctor-qwerty from the installed plugin |
| PASS | real goose: recipe validate passes for both installed recipes; rendering fills {{ recipe_dir }} with the installed folder and python=py sets cmd |
| PASS | recipe route (goose run --recipe <installed>/recipes/spindoctor-qwerty-task.yaml): the 6 tools are offered as spindoctor-qwerty__<tool> plus the developer shell; recipe instructions reach the system prompt |
| PASS | headless goose run: answer printed, 6 agent turns, 5 tool results returned |
| PASS | MCP tools via goose: function table, Bell run (ok, PDF report in the workspace), preset qc-001 ok |
| PASS | theory test from the chat via goose: verdict supported, 2 excerpts recorded, theory PDF on disk |
| PASS | shell fallback (developer extension's shell tool) runs the installed plugin's CLI: gate table |
| PASS | config.yaml route (entry from tools/goose_setup.py) + plugin skill: plain goose run offers spindoctor-qwerty__* tools and load_skill; the skill is listed in the system prompt |
| PASS | load_skill returns the SpinDoctor skill instructions; preset qc-002 runs through the config.yaml extension |
| PASS | shared E2E suite through the installed plugin's MCP server: SUMMARY 12/12 |
| PASS | removal (goose 1.54 has no plugin uninstall): deleting ~/.agents/plugins/spindoctor-qwerty and the config entry removes the skill |

## Shared end-to-end suite through the installed plugin: 12/12

Started with the installed plugin's MCP server: `python3 ~/.agents/plugins/spindoctor-qwerty/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py`.

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Clean-room copy (fresh folder, no git metadata): host check 17/17, shared E2E 12/12 - PASS
