#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - goose set-up helper
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Print the goose settings for THIS copy (absolute paths filled in). Changes nothing.

  python3 tools/goose_setup.py                  # human-readable
  python3 tools/goose_setup.py --python py      # Windows: the Python command goose should start (python3 | python | py | full path)
  python3 tools/goose_setup.py --json           # machine-readable

Prints: the config.yaml extension entry, a goose:// deeplink for goose Desktop, and the recipe commands. Standard library only.
"""
import json, os, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP = os.path.join(ROOT, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py")
RECIPE = os.path.join(ROOT, "recipes", "spindoctor-qwerty.yaml")
DESC = "SpinDoctor 3.1.2 quantum-circuit simulator (classical, not a quantum computer)"


def q(s):  # YAML double-quoted scalar
    return json.dumps(s)


def main():
    a = sys.argv[1:]
    py = a[a.index("--python") + 1] if "--python" in a else ("py" if os.name == "nt" else "python3")
    yaml = "\n".join([
        "extensions:",
        "  spindoctor-qwerty:",
        "    type: stdio",
        "    name: spindoctor-qwerty",
        "    display_name: SpinDoctor Qwerty",
        "    description: " + q(DESC),
        "    enabled: true",
        "    bundled: false",
        "    cmd: " + q(py),
        "    args: [" + q(MCP) + "]",
        "    envs: {}",
        "    env_keys: []",
        "    timeout: 600",
        "    available_tools: []", ""])
    link = "goose://extension?" + urllib.parse.urlencode([("cmd", py), ("arg", MCP), ("timeout", "600"), ("id", "spindoctor-qwerty"),
                                                         ("name", "SpinDoctor Qwerty"), ("description", DESC)], quote_via=urllib.parse.quote)
    pyp = [] if py == "python3" else ["--params", "python=" + py]
    sess = ["goose", "session", "--recipe", RECIPE] + pyp
    run = ["goose", "run", "--recipe", os.path.join(ROOT, "recipes", "spindoctor-qwerty-task.yaml"), "--params", "task=show the SpinDoctor functions"] + pyp
    if "--json" in a:
        print(json.dumps({"python": py, "mcp": MCP, "configYaml": yaml, "deeplink": link, "session": sess, "run": run}, indent=2)); return 0
    qa = lambda l: " ".join(x if x.replace("/", "").replace("-", "").replace("=", "").replace(".", "").replace("_", "").replace(":", "").isalnum() else q(x) for x in l)
    print("1) Easiest: start a session with the recipe (it adds the SpinDoctor extension for that session):\n\n   " + qa(sess))
    print("\n   Headless, one task:\n\n   " + qa(run))
    print("\n2) Always on: merge this into goose's config.yaml (`goose info` shows where it is; if the file already has an `extensions:`")
    print("   key, add only the `spindoctor-qwerty:` block under it), then restart goose:\n")
    print("\n".join("   " + l for l in yaml.splitlines()))
    print("\n3) goose Desktop: open this deeplink (paste it in a browser address bar):\n\n   " + link)
    print("\nThe skill comes with `goose plugin install https://github.com/LKVexa/spindoctor-qwerty-goose.git`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
