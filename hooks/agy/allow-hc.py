#!/usr/bin/env python3
"""Antigravity PreToolUse hook: keep a gamma agent's allow-list narrow.

Usage in hooks.json: ./allow-hc.py GAMMA   (GAMMA is the short name, e.g. argon)
Allows, as single unchained commands only:
  hc --skill | hc ls | hc wait ...            hc read/keys/kill/rm on its own workers (w-GAMMA-N)
  hc send to its own workers or to its parent (id in .team/parent-id)
  hc run that starts a worker named w-GAMMA-N running opencode or muse, with no bypass flags
  python3 -m unittest ...                      ls of relative paths inside the folder
  rm tests/test_MODULE_alt.py | rm tally/MODULE_alt.py | mv tally/MODULE_alt.py tally/MODULE.py
                                               (settling a race between two workers)
  date [+FORMAT]
It grants nothing by itself. The agent is launched with an allow-list for commands starting with
`hc`, `python3 -m unittest`, `ls`, `date`, `rm` and `mv`; this hook answers "force_ask" for any such command that is
not one of the forms above, so that it still goes to the parent for approval.
"""
import json, os, re, shlex, sys

def out(decision, reason=""):
    print(json.dumps({"decision": decision, "reason": reason})); sys.exit(0)

gamma = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    cmd = json.load(sys.stdin)["toolCall"]["args"]["CommandLine"]
except Exception:
    out("force_ask")
here = os.path.dirname(os.path.abspath(__file__))
try:
    parent = open(os.path.join(here, "..", ".team", "parent-id")).read().strip()
except OSError:
    parent = ""
if "`" in cmd or "$(" in cmd or "\n" in cmd.strip():
    out("force_ask")
try:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True); lex.whitespace_split = True
    toks = list(lex)
except ValueError:
    out("force_ask")
if not toks or any(t and set(t) <= set("();<>|&") for t in toks):
    out("force_ask")   # an unquoted shell operator: chained, piped or redirected
worker = re.compile(r"^w-%s-\d+$" % re.escape(gamma))
ok = False
if toks[0] == "hc" and len(toks) > 1:
    sub, rest = toks[1], toks[2:]
    names = [t for t in rest if not t.startswith("-")]
    if sub in ("--skill", "ls"):
        ok = True
    elif sub == "wait":
        ok = "--children" in rest or all(worker.match(n) or n.isdigit() for n in names)
    elif sub in ("read", "kill", "rm"):
        ok = bool(names) and worker.match(names[0]) and all(worker.match(n) or n.isdigit() for n in names)
    elif sub == "keys":
        ok = bool(names) and bool(worker.match(names[0]))
    elif sub == "send":
        ok = bool(names) and (bool(worker.match(names[0])) or (parent and names[0] == parent))
    elif sub == "run" and "--" in rest:
        i = rest.index("--"); opts, prog = rest[:i], rest[i + 1:]
        name = opts[opts.index("--name") + 1] if "--name" in opts and opts.index("--name") + 1 < len(opts) else ""
        while prog and (prog[0] == "env" or re.match(r"^[A-Z_]+=", prog[0])):
            prog = prog[1:]
        bad = any(re.search(r"dangerous|bypass|--force|--yolo|skip-permissions", t) for t in prog[:1] + [t for t in prog if t.startswith("--")])
        ok = bool(worker.match(name)) and bool(prog) and prog[0] in ("opencode", "muse") and not bad
elif toks[:3] == ["python3", "-m", "unittest"]:
    ok = True
elif toks[0] == "rm":
    ok = len(toks) == 2 and bool(re.match(r"^(tests/test_[a-z]+_alt|tally/[a-z]+_alt)\.py$", toks[1]))
elif toks[0] == "mv":
    m = re.match(r"^tally/([a-z]+)_alt\.py$", toks[1]) if len(toks) == 3 else None
    ok = bool(m) and toks[2] == "tally/%s.py" % m.group(1)
elif toks[0] == "date":
    ok = len(toks) <= 2 and all(t.startswith("+") for t in toks[1:])
elif toks[0] == "ls":
    ok = all(t.startswith("-") or not (t.startswith(("/", "~")) or ".." in t) for t in toks[1:])
out("ask" if ok else "force_ask", "" if ok else "not a routine command for this agent")
