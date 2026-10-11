# SpinDoctor Qwerty for goose

Adds the **SpinDoctor 3.1.2 quantum-circuit simulator** to [goose](https://goose-docs.ai), the open-source AI agent: `q.*` circuit
scripts (1-298 logical qubits), the 241 built-in presets, folders of command files (`q.folder`), and theory tests from a file, pasted
text or the chat itself, each with TXT, PDF, JSON and CSV reports. It runs on your computer through a local MCP extension.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - tested with goose CLI 1.54.0 - Python 3.8+, standard library only - no
network, no account and no keys for the extension itself (goose still needs whatever model provider you use).

## Install

**1. The plugin (skill + engine):**

```bash
goose plugin install https://github.com/LKVexa/spindoctor-qwerty-goose.git
```

goose clones the repo into `~/.agents/plugins/spindoctor-qwerty/` (Windows: `%USERPROFILE%\.agents\plugins\spindoctor-qwerty\`)
and imports the skill `spindoctor-qwerty:spindoctor-qwerty` (check with `goose skills list`). Add `--auto-update` to keep it current;
`goose plugin update` updates it by hand.

**2. The tools (MCP extension).** goose plugins carry skills and hooks, not MCP servers, so add the extension one of three ways:

- **Recipe, for a session (no editing):**

  ```bash
  goose session --recipe ~/.agents/plugins/spindoctor-qwerty/recipes/spindoctor-qwerty.yaml
  goose run --recipe ~/.agents/plugins/spindoctor-qwerty/recipes/spindoctor-qwerty-task.yaml --params "task=run preset qc-001"
  ```

  On Windows add `--params python=py` (or `python=python`). The recipe finds the engine next to itself (`{{ recipe_dir }}`).
  A recipe that lists extensions loads only those, so these recipes also enable goose's `developer` extension (shell and files).

- **Always on:** run `python3 ~/.agents/plugins/spindoctor-qwerty/tools/goose_setup.py` (Windows: `py` and the Windows path). It
  prints a `spindoctor-qwerty` entry for goose's `config.yaml` with the absolute engine path filled in (`goose info` shows where the
  file is; add only the `spindoctor-qwerty:` block under an existing `extensions:` key) and a `goose://extension?...` deeplink for goose
  Desktop. It changes nothing by itself.
- **goose configure:** Add Extension > Command-line Extension, name `spindoctor-qwerty`, command
  `python3 /absolute/path/to/spindoctor_mcp.py`, timeout 600.

Without the plugin, a plain clone works too: the recipes and `tools/goose_setup.py` use whatever folder they are in.

Requirements: Python 3.8 or newer. No packages to install.

## What's in the repo

| Path | What it is |
|---|---|
| `plugin.json` | goose Open Plugins manifest (name, version, license) |
| `skills/spindoctor-qwerty/` | Skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI and MCP server (`scripts/`), examples |
| `recipes/` | `spindoctor-qwerty.yaml` (interactive) and `spindoctor-qwerty-task.yaml` (headless, one task) |
| `tools/goose_setup.py` | Prints the config.yaml entry, deeplink and recipe commands for this copy |
| `FUNCTIONS.md` | The full function table with a runnable example for every command |
| `tests/` | Host check, shared end-to-end suite, local OpenAI-compatible stand-in, reference outputs |

No hooks: nothing runs on its own.

## Using it

- Ask in plain language ("show the SpinDoctor functions", "run a 3-qubit GHZ circuit"). Load the skill with
  `/skills spindoctor-qwerty:spindoctor-qwerty` or let goose load it when it fits.
- goose names the tools `spindoctor-qwerty__spindoctor_functions` and so on (the prefix is the extension name; if you add the
  extension with `--with-extension "python3 .../spindoctor_mcp.py"` the prefix becomes `python3__`, which also works).
- goose's permission mode decides whether it asks first: `auto` runs tools directly; `approve` and `smart_approve` ask.
- Pass absolute paths. Reports and state go to `~/spindoctor-workspace` unless a tool call passes `workspace` (or the extension sets
  `SPINDOCTOR_WORKSPACE` in `envs`).
- If the tools aren't available, the skill tells goose to run the CLI with the developer extension's shell tool:
  `python3 ~/.agents/plugins/spindoctor-qwerty/skills/spindoctor-qwerty/scripts/spindoctor_cli.py functions`.
- To remove it: delete `~/.agents/plugins/spindoctor-qwerty/` (goose 1.54 has no plugin uninstall command) and the
  `spindoctor-qwerty` entry from `config.yaml`, if you added one.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | Ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | Ask: "run preset qc-067 with shots=64" |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | Ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In goose, give the file's absolute path on your computer (or paste the text).
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command |
|---|---|
| Static checks | `python3 tests/goose_host_check.py` |
| Real goose CLI | `python3 tests/goose_host_check.py --goose "$(command -v goose)"` |

**Real host, scripted model.** The host check uses the real goose CLI (1.54.0 release binary) with a throwaway HOME, config and data
folders and no account: it installs a git copy of this repo with `goose plugin install`, checks `goose skills list`, validates and
renders the recipes, then runs headless `goose run` sessions against `tests/stub_llm.py`, a local scripted stand-in for an
OpenAI-compatible endpoint on 127.0.0.1 (`GOOSE_PROVIDER=openai`, `OPENAI_HOST`, placeholder key). Through goose's own MCP client it
shows the function table, runs a Bell circuit and presets qc-001/qc-002, tests a theory from the chat (verdict *supported*, PDF
written), runs the CLI through the shell tool, and loads the skill with `load_skill`, using both the recipe and the config.yaml
route. Then it runs the shared end-to-end suite through the installed plugin's MCP server and removes the plugin. Not tested: a real
model choosing the tools, goose Desktop and its deeplinks, interactive approval prompts, Windows, macOS. Results:
[E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). This project is not affiliated with the goose project.
