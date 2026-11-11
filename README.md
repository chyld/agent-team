# Agent team

A team of AI agents run through `hc`. Run `hc --skill` before you start anyone.

| # | Level | Harness | Model | Reasoning | Free? |
|---|---|---|---|---|---|
| 0 | alpha | `claude` | `claude-fable-5-2` | high | no |
| 1 | beta | `claude` | `claude-opus-5-5` | high | no |
| 2 | gamma | `claude` | `claude-sonnet-5-5` | high | no |
| 3 | gamma | `claude` | `claude-haiku-5-5` | high | no |
| 4 | gamma | `codex` | `gpt-6.1-sol` | high | no |
| 5 | gamma | `codex` | `gpt-6.1-terra` | high | no |
| 6 | gamma | `grok` | `grok-4.7` | high | no |
| 7 | gamma | `agy` | `gemini-4-argon` | high | no |
| 8 | worker | `muse` | `muse-ember-1.0` | high | no |
| 9 | worker | `opencode` | `opencode-go/minimax-m3.1-flash` | high | no |
| 10 | worker | `opencode` | `opencode-go/glm-5.3-flash` | high | no |
| 11 | worker | `opencode` | `opencode-go/kimi-k3.1-pro` | high | no |
| 12 | worker | `opencode` | `opencode-go/hy4` | high | no |
| 13 | worker | `opencode` | `opencode/beam-free` | high | 🟢 yes |
| 14 | worker | `opencode` | `opencode/deepseek-v4.1-flash-free` | high | 🟢 yes |
| 15 | worker | `opencode` | `opencode/flint-40b-free` | high | 🟢 yes |
| 16 | worker | `opencode` | `opencode/glm-5.3-flash-free` | high | 🟢 yes |
| 17 | worker | `opencode` | `opencode/iceman-free` |  | 🟢 yes |
| 18 | worker | `opencode` | `opencode/inkling-2-small-free` | high | 🟢 yes |
| 19 | worker | `opencode` | `opencode/longcat-2.5-free` |  | 🟢 yes |
| 20 | worker | `opencode` | `opencode/mimo-v2.6-flash-free` |  | 🟢 yes |
| 21 | worker | `opencode` | `opencode/nemotron-3.5-lightning-free` |  | 🟢 yes |
| 22 | worker | `opencode` | `opencode/nemotron-3.5-super-vl-free` | high | 🟢 yes |
| 23 | worker | `opencode` | `opencode/minimax-m3.1-flash-free` | high | 🟢 yes |
| 24 | worker | `opencode` | `openrouter/baidu/ernie-5.5-flash-preview:free` |  | 🟢 yes |
| 25 | worker | `pi` | `deeprelay/deeprelay/deepseek-v4.1-flash` | high | no |
| 26 | worker | `pi` | `deeprelay/deeprelay/glm-5.3-flash` | high | no |

Agents 8 to 26 are the worker pool. A blank reasoning cell means the model's default.

## Hierarchy

**The user decides the hierarchy.** Before a build, alpha asks the user which agents take part, at
which level, and who reports to whom, and starts no one until the user has answered. No agent
changes it on its own. The levels in the table are the arrangement used so far:

```
alpha ── beta ── six gamma agents ── workers (dealt at random from the pool)
```

- **Alpha** takes the task from the user, writes the spec and beta's brief, and checks the result
  with its own acceptance tests, which the team never sees.
- **Beta** writes the shared pieces, starts the gamma agents, deals the workers, approves what
  gamma asks for, integrates, and reports to alpha.
- **Gamma** agents own one part each. They start workers and check what comes back; they do not
  write the files themselves.
- **Workers** write exactly one file each and start no one.
- Nobody skips a level, in either direction. Each level cleans up its own terminals, and only
  those.

## A build

1. **Alpha** writes `SPEC.md` and `brief-beta.md` in a new folder, writes acceptance tests
   elsewhere, and starts beta with `Read brief-beta.md and follow it exactly.`
2. **Beta** writes the shared types, deals the workers, writes one brief per gamma agent
   (`.team/brief-g-NAME.md`) and launches them all. It logs each event with a time in
   `.team/progress.log`, which is how alpha follows the build.
3. **Each gamma agent starts four workers at once**, two racing on the code and two on the tests.
   Its first dealt worker writes `pkg/MODULE.py` and `tests/test_MODULE_alt.py`; its second writes
   `tests/test_MODULE.py` and `pkg/MODULE_alt.py`. The first code file to arrive wins and the other
   racer is killed. Both test files are kept if both pass.
4. **Gamma runs the tests** and sends precise corrections to the worker whose file is wrong. It
   edits a file itself only after two failed rounds.
5. **Gamma reads the module against the spec once**, for at most two minutes, and sends at most
   one correction, quoting the spec sentence the code breaks. `grok` and `agy` skip this step and
   beta does it for them.
6. **Gamma kills and removes its workers and reports to beta.** Beta integrates, runs the full
   suite, cleans up and reports to alpha. A missing part means the result is incomplete: reassign
   it or report it as missing.

**Dealing.** Beta shuffles the worker pool once per build. Each gamma agent gets two workers and
the rest are the reserve. If a pair has `muse`, it goes second; otherwise put a paid model second.

```sh
# the worker rows of the table above, shuffled, as "harness model"
awk -F' *[|] *' '{ gsub(/`/, "") } $3 == "worker" {
  print $4, $5 ($4 == "opencode" && $6 == "high" ? "#high" : "") }' /path/to/agent-team/README.md | shuf
```

**Stalls.** A worker has stalled when neither racing file exists after three minutes (four for
tests). A stuck worker never changes status, so beta reads the workers' screens itself at three
and five minutes. It saves the screen (`hc read NAME --lines 0 > .team/stall-NAME.txt`), kills the
worker, and gives the gamma agent the exact launch command for a replacement: first a worker that
has already delivered in this build, then the reserve.

## Launch commands

Every agent is one command, run interactively (never `claude -p`, `codex exec`, `pi -p`,
`opencode run` and the like):

```sh
hc run --bg --name NAME --cwd DIR -- HARNESS_COMMAND
```

| Harness | `HARNESS_COMMAND` for a gamma agent |
|---|---|
| `claude` | `claude --model MODEL --effort high "PROMPT"` |
| `codex` | `codex --no-daemon -m MODEL -c model_reasoning_effort='"high"' -s workspace-write -a on-request -c 'sandbox_workspace_write.network_access=true' "PROMPT"` |
| `grok` | `grok -m MODEL --effort high --permission-mode acceptEdits --allow 'Bash(hc:*)' --allow 'Bash(python3 -m unittest:*)' "PROMPT"` |
| `agy` | `agy --model MODEL --effort high --mode accept-edits --settings '{"permissions":{"allow":["command(hc)","command(python3 -m unittest)","command(ls)","command(date)","command(rm)","command(mv)"]}}' -i "PROMPT"` |

The `codex` and `agy` flags grant their routine `hc` commands so that beta is not asked to approve
each one. That grant is the user's decision; agents never widen permissions on their own.

- **`codex`:** its sandbox needs network access to reach the hc core, and with it on none of its
  commands prompt. Say "no network use" in its brief and check afterwards what it touched.
- **`agy`:** copy [`hooks/agy/`](hooks/agy) into the work folder as `.agents/hooks.json` and
  `.agents/allow-hc.py`. The hook limits the allow-list to single, unchained commands on the
  agent's own workers (`w-GAMMA-N`). Set the agent's short name in `hooks.json`, and have beta
  write its own terminal id into `.team/parent-id`.

Workers (`MODEL` is the id from the table; for `opencode`, add `#high` when the table lists high
reasoning):

```sh
# opencode: may write one file, asks for everything else
hc run --bg --name NAME --cwd "$PWD" -- env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL","permission":{"edit":{"*":"ask","ABS_PATH":"allow","REL_PATH":"allow","./REL_PATH":"allow"},"bash":{"*":"ask"},"webfetch":"deny"}}' opencode --standalone --prompt "TASK"

# muse: its own sandbox is the limit; do not disable it
hc run --bg --name NAME --cwd "$PWD" -- muse --model muse-ember-1.0 --effort high "TASK"

# pi: no prompts and no sandbox, so the task text is its only limit; check afterwards what it touched
hc run --bg --name NAME --cwd "$PWD" -- pi --model MODEL --thinking high "TASK"
```

## Worker tasks

What matters is a small task and being told to start writing.

**Code:**

> Write only `pkg/MODULE.py` for the MODULE section of `SPEC.md`, following the signatures
> exactly and using the shared types. The folders already exist. Read only `SPEC.md` and the
> types file. Do not plan at length: start writing within one minute and finish within two, in
> one go. Run no commands. Say `DONE` when the file is written.

**Tests:**

> Write only `tests/test_MODULE.py` for the MODULE section of `SPEC.md`. The folders already
> exist. Use `unittest`. Write at most 15 tests: first every example the spec states, with the
> exact values it gives, then one or two simple cases per function. Do not work out long expected
> strings by hand; where the spec gives no exact output, assert on something simple. Do not plan
> at length: write the file within two minutes, in one go. If importing another module fails for
> any reason (`except Exception`), use a small stand-in. Run no commands. Say `DONE` when the
> file is written.

For the `_alt` racers, name the `_alt` file and add "it is renamed later; do not write
`MODULE.py`".

## What every brief must say

- Who the agent reports to, as a literal terminal id (`hc send t3 '...'`), and no one else.
- Which agents it may start, by name, harness and model, with the exact launch commands.
- To run `hc --skill` first, and to run one command per call, never chained.
- To wait with `hc wait --children all --timeout 60`, never sleep, and after each wait to read
  each worker's screen (`hc read NAME --lines 0`) and check whether its file exists.
- To refuse a worker's request for anything but its one file.
- To put `hc send` text in single quotes (double quotes eat `$1.00`).
- To touch only its own files, and to kill and remove what it started before reporting.
- For beta: what it may approve, once each, never "always allow" and never `--force`: the `hc`
  commands and test runs its gamma agents' briefs call for, and nothing else. After a refusal it
  sends `skip that step and continue with your brief`.

## Things to watch for

| Harness | Behaviour |
|---|---|
| `claude` | Runs in auto mode: fastest, never asks, so its brief is its only limit. In a new folder it stops at a trust prompt that is not flagged: `hc keys NAME down enter`. |
| `codex` | Careful reviewer that invents requirements unless held to the one-pass, quote-the-spec rule. Trust prompt: `enter`. |
| `grok` | Queues every message until its turn ends, and reviews slowly. Give it no review and no report file; its report is one `hc send`. Still asks before `rm`, `mv` and redirects. |
| `agy` | Opens with a chained command that searches the home folder; refuse it and send "continue". Slow to react. Trust prompt: `enter`. |
| `pi` | Worker only. Never asks and has no sandbox, so its task is its only limit: check afterwards what it touched. No trust prompt in a new folder. It shows `idle` before its first turn, so a wait sent right after launch returns at once: wait again. It has not yet run as a worker in a build. |
| `muse` | Worker only: its sandbox blocks `hc run` and `hc send`. Trust prompt: `enter`. It answers in its chat and ends its turn. |
| `opencode` | Status is unreliable in both directions; read the screen and check the file. With no permission block it asks for nothing. |

- **Read every screen right after launch.** Trust prompts are not reported as blocked. Accept
  trust for the work folder only.
- **After each approval, read the screens of every blocked child.** A child that goes from one
  prompt straight to the next does not wake `hc wait`.
