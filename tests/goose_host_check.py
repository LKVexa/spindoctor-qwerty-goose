#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - goose host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run from the repo root:

  python3 tests/goose_host_check.py                                   # static checks only
  python3 tests/goose_host_check.py --goose "$(command -v goose)" [--out tests/host_check.json]

Static: plugin.json, skill, recipes, tools/goose_setup.py output, and the MCP server answering `initialize`.
Real host (--goose): with a throwaway HOME / config / data folders, `goose plugin install <a git copy of this repo>`, `goose skills list`,
`goose recipe validate`, then headless `goose run` sessions against tests/stub_llm.py, a local scripted stand-in for an OpenAI-compatible
endpoint on 127.0.0.1 (GOOSE_PROVIDER=openai + OPENAI_HOST, placeholder key: no account, nothing leaves the machine). Covers the recipe
route and the config.yaml route, the 6 MCP tools, the plugin skill (load_skill), the shell fallback, the shared end-to-end suite through
the installed plugin's engine, and removal. Standard library only.
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.parse
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SK = os.path.join(ROOT, "skills", "spindoctor-qwerty"); MCP = os.path.join(SK, "scripts", "spindoctor_mcp.py")
TOOLS = ["spindoctor_functions", "spindoctor_list_presets", "spindoctor_report", "spindoctor_run_preset", "spindoctor_run_script", "spindoctor_test_theory"]
N = lambda t: "spindoctor-qwerty__" + t
R = []
OK = lambda s: bool(re.search(r'"ok":\s*true', s or ""))


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


def mcp_init(cmd, timeout=60):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "1"}}}) + "\n"
    p = subprocess.run(cmd, input=req.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def setup_json(root, *extra):
    return json.loads(subprocess.run([sys.executable, os.path.join(root, "tools", "goose_setup.py"), "--json"] + list(extra), stdout=subprocess.PIPE, check=True).stdout)


def static():
    p = json.load(open(os.path.join(ROOT, "plugin.json"), encoding="utf-8"))
    T("plugin.json (Open Plugins manifest): name spindoctor-qwerty, version 1.1.0, description, license GPL-3.0-or-later, author",
      p.get("name") == "spindoctor-qwerty" and p.get("version") == "1.1.0" and p.get("description") and p.get("license") == "GPL-3.0-or-later"
      and p.get("author", {}).get("name") == "RUSSELL PHILIP SMITHSON", p)
    sk = open(os.path.join(SK, "SKILL.md"), encoding="utf-8").read(); fm = sk.split("---")[1]
    T("skill skills/spindoctor-qwerty/SKILL.md: front matter (name, description, license) + honest limits; no hooks (nothing runs on its own)",
      "name: spindoctor-qwerty" in fm and "description:" in fm and "license: GPL-3.0-or-later" in fm and "not a quantum computer" in sk
      and "Droid" not in sk and not os.path.exists(os.path.join(ROOT, "hooks")), fm[:200])
    rs = {}
    for f in ("spindoctor-qwerty.yaml", "spindoctor-qwerty-task.yaml"):
        rs[f] = open(os.path.join(ROOT, "recipes", f), encoding="utf-8").read()
    T("recipes: stdio extension spindoctor-qwerty = {{ python }} (default python3) + {{ recipe_dir }}/../skills/.../spindoctor_mcp.py, 600 s; task recipe adds prompt {{ task }}; honest limits",
      all('cmd: "{{ python }}"' in s and '"{{ recipe_dir }}/../skills/spindoctor-qwerty/scripts/spindoctor_mcp.py"' in s and "timeout: 600" in s and "default: python3" in s
          and "never quantum hardware" in s for s in rs.values()) and 'prompt: "{{ task }}"' in rs["spindoctor-qwerty-task.yaml"] and "prompt:" not in rs["spindoctor-qwerty.yaml"], "")
    j = setup_json(ROOT); jw = setup_json(ROOT, "--python", "py")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(j["deeplink"]).query)
    T("tools/goose_setup.py: config.yaml entry with this copy's absolute engine path, deeplink (cmd/arg/id/name/timeout) round-trips, --python py for Windows",
      os.path.isfile(j["mcp"]) and json.dumps(j["mcp"]) in j["configYaml"] and "    type: stdio" in j["configYaml"] and q.get("arg") == [j["mcp"]]
      and q.get("cmd") == [j["python"]] and q.get("id") == ["spindoctor-qwerty"] and q.get("timeout") == ["600"] and 'cmd: "py"' in jw["configYaml"]
      and jw["session"][-2:] == ["--params", "python=py"], j["configYaml"][:300])
    rc, out, err = mcp_init([sys.executable, MCP])
    T("MCP server starts (initialize answered, server spindoctor-qwerty 1.1.0)", '"spindoctor-qwerty"' in out and '"1.1.0"' in out, (rc, out[:200], err[-300:]))


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def content(c):  # tool results may arrive as a string or a list of text parts
    if isinstance(c, list): return "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return c if isinstance(c, str) else json.dumps(c)


def real(goose):
    tmp = tempfile.mkdtemp(prefix="sdq-goose-"); home = os.path.join(tmp, "home"); work = os.path.join(tmp, "work"); ws = os.path.join(tmp, "ws")
    for d in (home, work): os.makedirs(d)
    port = free_port(); log = os.path.join(tmp, "stub.jsonl"); script = os.path.join(tmp, "script.json")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GOOSE", "OPENAI", "XDG_", "SPINDOCTOR", "ANTHROPIC"))}
    env.update(HOME=home, USERPROFILE=home, XDG_CONFIG_HOME=os.path.join(home, ".config"), XDG_DATA_HOME=os.path.join(home, ".local", "share"),
               XDG_STATE_HOME=os.path.join(home, ".local", "state"), XDG_CACHE_HOME=os.path.join(home, ".cache"), NO_COLOR="1",
               GOOSE_PROVIDER="openai", GOOSE_MODEL="gpt-4o-mini", OPENAI_HOST="http://127.0.0.1:%d" % port, OPENAI_API_KEY="local-stub",
               GOOSE_DISABLE_KEYRING="1", GOOSE_TELEMETRY_ENABLED="false", GOOSE_MODE="auto")
    run = lambda args, t=300: subprocess.run([goose] + args, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=t)
    stub = None
    try:
        v = run(["--version"], t=60).stdout.decode().strip()
        src = os.path.join(tmp, "src")
        shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(".git", "__pycache__", "e2e_results.json", "host_check.json"))
        g = lambda *a: subprocess.run(["git", "-c", "user.name=check", "-c", "user.email=check@example.test"] + list(a), cwd=src, stdout=subprocess.DEVNULL, check=True)
        g("init", "-q"); g("add", "-A"); g("commit", "-qm", "snapshot")
        r = run(["plugin", "install", src]); o = r.stdout.decode("utf-8", "replace")
        inst = os.path.join(home, ".agents", "plugins", "spindoctor-qwerty")
        T("real goose %s (no account): plugin install <git repo> -> open-plugins plugin 1.1.0 in ~/.agents/plugins/spindoctor-qwerty, skill spindoctor-qwerty:spindoctor-qwerty" % v,
          r.returncode == 0 and "Installed open-plugins plugin 'spindoctor-qwerty' (1.1.0)" in o and "spindoctor-qwerty:spindoctor-qwerty" in o
          and os.path.isfile(os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py")), o[-400:])
        o = run(["skills", "list"], t=120).stdout.decode("utf-8", "replace")
        T("real goose: skills list shows spindoctor-qwerty:spindoctor-qwerty from the installed plugin", "spindoctor-qwerty:spindoctor-qwerty" in o and inst in o, o[-400:])
        rec = os.path.join(inst, "recipes", "spindoctor-qwerty.yaml"); rect = os.path.join(inst, "recipes", "spindoctor-qwerty-task.yaml")
        ok = all(b"recipe file is valid" in run(["recipe", "validate", f], t=60).stdout for f in (rec, rect))
        rr = run(["run", "--recipe", rect, "--params", "task=x", "--params", "python=py", "--render-recipe"], t=60).stdout.decode("utf-8", "replace")
        T("real goose: recipe validate passes for both installed recipes; rendering fills {{ recipe_dir }} with the installed folder and python=py sets cmd",
          ok and "cmd: py" in rr and os.path.join(inst, "recipes") + "/../skills/spindoctor-qwerty/scripts/spindoctor_mcp.py" in rr, rr[-400:])

        def session(steps, args):
            json.dump(steps, open(script, "w")); open(log, "w").close()
            nonlocal stub
            if stub: stub.kill(); stub.wait()
            stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_llm.py"), str(port), log, script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            r = run(args + ["--no-session"], t=900); o = r.stdout.decode("utf-8", "replace")
            recs = [json.loads(l) for l in open(log)]
            agent = [x for x in recs if x["tools"]]
            res = {}
            if agent:  # tool results are in call order in the last agent request
                names = [s["tool"] for s in steps if "tool" in s]
                for n, c in zip(names, agent[-1]["tool_results"]): res.setdefault(n, []).append(content(c))
            return r.returncode, o, agent, res

        thy = {"source": "chat", "text": "Theory: H then CX makes a Bell state; only 00 and 11, about half each.",
               "excerpts": ["User: does H then CX entangle two qubits?", "Assistant: yes, a Bell state."], "hypothesis": "H(0) then CX(0,1) prepares a Bell state",
               "prediction": "P(00)=P(11)=0.5", "script": "q.circuit new th 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z",
               "checks": [{"kind": "probability", "outcome": x, "expected": 0.5, "tolerance": 0.05} for x in ("00", "11")], "workspace": ws}
        cli = os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_cli.py")
        steps = [{"tool": N("spindoctor_functions"), "args": {}},
                 {"tool": N("spindoctor_run_script"), "args": {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z", "workspace": ws}},
                 {"tool": N("spindoctor_run_preset"), "args": {"preset_id": "qc-001", "workspace": ws}},
                 {"tool": N("spindoctor_test_theory"), "args": thy},
                 {"tool": "shell", "args": {"command": 'python3 "%s" functions gates' % cli}},
                 {"text": "Done. SpinDoctor is a classical simulation, not quantum hardware."}]
        rc, o, agent, res = session(steps, ["run", "--recipe", rect, "--params", "task=Show the SpinDoctor functions, run a Bell circuit and preset qc-001, and test the Bell theory we discussed."])
        offered = set(agent[0]["tools"]) if agent else set()
        sysm = agent[0]["system"] or "" if agent else ""
        T("recipe route (goose run --recipe <installed>/recipes/spindoctor-qwerty-task.yaml): the 6 tools are offered as spindoctor-qwerty__<tool> plus the developer shell; recipe instructions reach the system prompt",
          all(N(t) in offered for t in TOOLS) and "shell" in offered and "classical FP64 simulation on the user's computer" in sysm, sorted(offered))
        G = lambda n: (res.get(n) or [""])[0]
        T("headless goose run: answer printed, %d agent turns, 5 tool results returned" % len(agent),
          rc == 0 and "classical simulation" in o and len(agent) == len(steps) and len(agent[-1]["tool_results"]) == 5 if agent else False, o[-300:])
        T("MCP tools via goose: function table, Bell run (ok, PDF report in the workspace), preset qc-001 ok",
          "| Function |" in G(N("spindoctor_functions")) and OK(G(N("spindoctor_run_script"))) and ".pdf" in G(N("spindoctor_run_script"))
          and ws in G(N("spindoctor_run_script")) and "qc-001" in G(N("spindoctor_run_preset")), {k: v[0][:160] for k, v in res.items()})
        th = G(N("spindoctor_test_theory")); pdfs = re.findall(r'"([^"]+\.pdf)', th)
        T("theory test from the chat via goose: verdict supported, 2 excerpts recorded, theory PDF on disk",
          re.search(r'"verdict":\s*"supported"', th) and re.search(r'"excerptsRecorded":\s*2', th) and pdfs and os.path.isfile(pdfs[0]), th[:300])
        T("shell fallback (developer extension's shell tool) runs the installed plugin's CLI: gate table", "Gate set" in G("shell"), G("shell")[:300])

        # config.yaml route: the entry printed by the installed copy's goose_setup.py
        cfgd = os.path.join(home, ".config", "goose"); os.makedirs(cfgd, exist_ok=True)
        open(os.path.join(cfgd, "config.yaml"), "w").write(setup_json(inst)["configYaml"])
        steps = [{"tool": "load_skill", "args": {"name": "spindoctor-qwerty:spindoctor-qwerty"}},
                 {"tool": N("spindoctor_run_preset"), "args": {"preset_id": "qc-002", "workspace": ws}}, {"text": "Preset done (classical simulation)."}]
        rc, o, agent, res = session(steps, ["run", "--text", "Load the SpinDoctor skill and run preset qc-002."])
        offered = set(agent[0]["tools"]) if agent else set()
        T("config.yaml route (entry from tools/goose_setup.py) + plugin skill: plain goose run offers spindoctor-qwerty__* tools and load_skill; the skill is listed in the system prompt",
          all(N(t) in offered for t in TOOLS) and "load_skill" in offered and "spindoctor-qwerty:spindoctor-qwerty" in (agent[0]["system"] or "" if agent else ""), sorted(offered))
        T("load_skill returns the SpinDoctor skill instructions; preset qc-002 runs through the config.yaml extension",
          "q.circuit" in G("load_skill") and "classical" in G("load_skill") and "qc-002" in G(N("spindoctor_run_preset")) and rc == 0,
          {k: v[0][:200] for k, v in res.items()})
        e2e = os.path.join(HERE, "e2e_results.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server", sys.executable, os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py"),
                            "--examples", os.path.join(SK, "examples", "theory"), "--out", e2e], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3600, cwd=work)
        t = r.stdout.decode("utf-8", "replace"); mm = re.search(r"SUMMARY (\d+)/(\d+)", t)
        T("shared E2E suite through the installed plugin's MCP server: %s" % (mm.group(0) if mm else "?"),
          r.returncode == 0 and mm and mm.group(1) == mm.group(2), "\n".join(l for l in t.splitlines() if l.startswith("FAIL"))[-500:])
        shutil.rmtree(inst); os.remove(os.path.join(cfgd, "config.yaml"))
        o = run(["skills", "list"], t=120).stdout.decode("utf-8", "replace")
        T("removal (goose 1.54 has no plugin uninstall): deleting ~/.agents/plugins/spindoctor-qwerty and the config entry removes the skill", "spindoctor-qwerty" not in o, o[-300:])
    finally:
        if stub: stub.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    static()
    if opt.get("--goose"): real(os.path.abspath(opt["--goose"]))
    outp = opt.get("--out", os.path.join(HERE, "host_check.json"))
    json.dump({"passed": sum(r["pass"] for r in R), "total": len(R), "python": sys.version.split()[0], "checks": R}, open(outp, "w"), indent=1)
    print("HOST CHECK %d/%d passed" % (sum(r["pass"] for r in R), len(R)))
    return 0 if all(r["pass"] for r in R) else 1


if __name__ == "__main__":
    sys.exit(main())
