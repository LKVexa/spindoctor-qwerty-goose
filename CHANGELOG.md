# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics, CSV report copies and measurement-CSV fitting equations. All 241
  presets replayed. Tools `spindoctor_functions` (function table, marked read-only) and `spindoctor_test_theory` (theory testing
  from a file, pasted text or the chat, with TXT+JSON+PDF theory reports).
- **Installable.** 1.0 was only a `config.yaml` snippet. The repo root is now a goose Open Plugin (`plugin.json` + the
  `spindoctor-qwerty` skill with the bundled engine), so `goose plugin install https://github.com/LKVexa/spindoctor-qwerty-goose.git`
  installs the skill and engine in one step.
- **Recipes.** `recipes/spindoctor-qwerty.yaml` (interactive) and `recipes/spindoctor-qwerty-task.yaml` (headless, `--params task=...`)
  add the MCP extension for the session with `{{ recipe_dir }}`, so no path editing; `--params python=py` on Windows.
- **No personal path.** 1.0's snippet hard-coded a path on the author's PC and `cmd: python` (missing on many macOS/Linux systems).
  `tools/goose_setup.py` now prints the config entry, a goose Desktop deeplink and the recipe commands with this copy's absolute paths
  and the right Python command.
- **Skill.** 1.0 had no instructions for goose ("MCP config only"). The skill tells goose how to use the tools, test theories, run
  folders, fall back to the CLI through the shell tool, and state the honest limits; the recipes carry the same instructions.
- Docs point to goose-docs.ai and the aaif-goose project; qubit limits updated from 29 to 298 logical qubits.
- Tests: `tests/goose_host_check.py` (static checks, and the real goose CLI: plugin install, skills list, recipe validate/render,
  headless runs through the recipe and the config route against a local OpenAI-compatible stand-in, load_skill, shell fallback, the
  shared end-to-end suite, removal).
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/config.yaml` (a stdio extension entry with a fixed path) and the bundled engine.
