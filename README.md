# Agent team

A team of AI agents run through `hc`, three levels deep. **Read the hc skill first:** run
`hc --skill` before you start anyone.

| # | Level | Harness | Model | Reasoning |
|---|---|---|---|---|
| 0 | alpha | `claude` | `claude-fable-5-2` | high |
| 1 | beta | `claude` | `claude-opus-5-5` | high |
| 2 | gamma | `claude` | `claude-sonnet-5-5` | high |
| 3 | gamma | `claude` | `claude-haiku-5-5` | high |
| 4 | gamma | `codex` | `gpt-6.1-sol` | high |
| 5 | gamma | `codex` | `gpt-6.1-terra` | high |
| 6 | gamma | `grok` | `grok-4.7` | high |
| 7 | gamma | `agy` | `gemini-4-argon` | high |
| 8 | gamma | `pi` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | high |
| 9–26 | worker | `muse`, 15 `opencode` models and 2 `pi` models | see [the pool](#dealing-the-workers) | |

## Chain of command

```
alpha ── beta ── seven gamma agents ── workers (dealt at random from the pool)
```

- **Alpha** takes the task from the user, writes the spec and beta's brief, and checks the result
  with its own acceptance tests, which the team never sees.
- **Beta** writes the shared pieces, starts the gamma agents, deals the workers, approves what
  gamma asks for, integrates, and reports to alpha.
- **Gamma** agents own one part each. They start workers, check what comes back, and report to
  beta. They do not write the files themselves.
- **Workers** write exactly one file each and start no one.
- Nobody skips a level, in either direction.

## How to run a build

1. **Alpha** writes `SPEC.md` and `brief-beta.md` in a new folder, writes acceptance tests
   elsewhere, and starts beta with `Read brief-beta.md and follow it exactly.`
2. **Beta** writes the shared types first, then [deals the workers](#dealing-the-workers), writes
   one brief file per gamma agent (`.team/brief-g-NAME.md`) and launches all seven.
3. **Each gamma agent starts four workers at once**, two racing on the code and two on the tests:

   | Worker | Writes | Model |
   |---|---|---|
   | `w-GAMMA-1` | `pkg/MODULE.py` | first dealt worker |
   | `w-GAMMA-2` | `tests/test_MODULE.py` | second dealt worker |
   | `w-GAMMA-3` | `tests/test_MODULE_alt.py` | first dealt worker |
   | `w-GAMMA-4` | `pkg/MODULE_alt.py` | second dealt worker |

4. **The first file to arrive wins.** For the code: if the `_alt` file is first, kill the other
   code worker, then `mv` it into place; otherwise kill the `_alt` worker and delete its file. For
   the tests: use the first, keep the second if it also passes, delete it if it fails.
5. **Gamma runs the tests** and sends precise corrections to the worker whose file is wrong. It
   edits a file itself only after two failed rounds.
6. **Gamma reads the module against the spec once**, for at most two minutes, and sends at most
   one correction. Every point must quote the spec sentence the code breaks; doubts go in its
   report. `grok` and `agy` skip this step and beta does it for them.
7. **Gamma kills and removes its workers and reports to beta**; beta integrates, runs the full
   suite, cleans up and reports to alpha.

Six builds of the same small Python package went from 23 minutes and 102 approvals to 11 minutes
and 2 approvals with these rules.

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
| `pi` | `pi --model MODEL --thinking high "PROMPT"` |

The `codex` and `agy` flags grant them their routine `hc` commands so that beta is not asked to
approve each one. That grant is the user's decision; agents never widen permissions on their own.

- **`codex`:** its sandbox cannot reach the hc core without network access. With it on, none of
  its commands prompt, so say "no network use" in its brief and check afterwards what it touched.
- **`agy`:** copy [`hooks/agy/`](hooks/agy) into the work folder as `.agents/hooks.json` and
  `.agents/allow-hc.py`. The hook narrows the allow-list to single, unchained commands on the
  agent's own workers (`w-GAMMA-N`); anything else still prompts. Set the agent's short name in
  `hooks.json`, and have beta write its own terminal id into `.team/parent-id`.
- **`pi`:** it has no approval prompts and no sandbox, so none of its commands prompt. Say what
  it may touch in its brief and check afterwards what it touched. `MODEL` is the full id from
  the table above, with the provider in front.

Workers:

```sh
# opencode: may write one file, asks for everything else
hc run --bg --name NAME --cwd "$PWD" -- env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL","permission":{"edit":{"*":"ask","ABS_PATH":"allow","REL_PATH":"allow","./REL_PATH":"allow"},"bash":{"*":"ask"},"webfetch":"deny"}}' opencode --standalone --prompt "TASK"

# muse: its own sandbox is the limit; do not disable it
hc run --bg --name NAME --cwd "$PWD" -- muse --model muse-ember-1.0 --effort high "TASK"

# pi: no prompts and no sandbox, so the task text is its only limit; check afterwards what it touched
hc run --bg --name NAME --cwd "$PWD" -- pi --model MODEL --thinking high "TASK"
```

`MODEL` for `opencode` is the id from the pool below, including `#high` where it is listed. For
`pi` it is the id from the pool as written.

## Dealing the workers

Beta shuffles the pool once per build. Each gamma agent gets two workers and four sit out as the
reserve. If the pair has `muse`, it is the second worker; otherwise put a paid model second.

```sh
pool=(
  'muse muse-ember-1.0'
  'opencode openrouter/deepseek/deepseek-v4.1-flash-1017#high'
  'opencode opencode-go/minimax-m3.1-flash#high'
  'opencode opencode-go/glm-5.3-flash#high'
  'opencode opencode-go/kimi-k3.1-pro#high'
  'opencode opencode-go/hy4#high'
  'opencode opencode/beam-free#high'
  'opencode opencode/deepseek-v4.1-flash-free#high'
  'opencode opencode/flint-40b-free#high'
  'opencode opencode/glm-5.3-flash-free#high'
  'opencode opencode/iceman-free'
  'opencode opencode/inkling-2-small-free#high'
  'opencode opencode/longcat-2.5-free'
  'opencode opencode/mimo-v2.6-flash-free'
  'opencode opencode/nemotron-3.5-lightning-free'
  'opencode opencode/nemotron-3.5-super-vl-free#high'
  'pi deeprelay/deeprelay/deepseek-v4.1-flash'
  'pi deeprelay/deeprelay/glm-5.3-flash'
)
gamma=(sonnet haiku sol terra grok argon ultra)
mapfile -t deal < <(printf '%s\n' "${pool[@]}" | shuf)
for i in "${!gamma[@]}"; do
  echo "${gamma[i]}: [${deal[2*i]}] [${deal[2*i+1]}]"
done
printf 'sits out: [%s]\n' "${deal[@]:14}"
```

A stall is when neither racing file exists after three minutes (four for tests). Beta then hands
the gamma agent a replacement: first a worker that has already delivered in this build, then the
reserve. Beta writes the exact launch command into a file and tells the gamma agent to follow it.

## Worker tasks

No model is reliably fast or slow; what matters is a small task and being told to start writing.

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
- To run `hc --skill` first, one command per call, never chained.
- To wait with `hc wait --children all --timeout 60`, never sleep, and after each wait read each
  worker's screen (`hc read NAME --lines 0`) and check whether its file exists.
- To reject a worker's prompt for anything but its one file, and tell it to write only its file.
- To put `hc send` text in single quotes (double quotes eat `$1.00`).
- To touch only its own files, and to kill and remove what it started before reporting.
- Beta's brief also lists what it may approve, once each, never "always allow" and never
  `--force`: the `hc` commands and test runs its gamma agents' briefs call for, and nothing else.
  After a refusal it sends `skip that step and continue with your brief`.

## Things to watch for

| Harness | Behaviour |
|---|---|
| `claude` | Runs in auto mode: fastest, never asks, so its brief is its only limit. In a new folder it stops at a trust prompt that is not flagged: `hc keys NAME down enter`. |
| `codex` | Careful reviewer that invents requirements unless held to the one-pass, quote-the-spec rule. Trust prompt: `enter`. |
| `grok` | Queues every message until its turn ends, and reviews slowly. Give it no review and no report file; its report is one `hc send`. Still asks before `rm`, `mv` and redirects. |
| `agy` | Opens with a chained command that searches the home folder; refuse it and send "continue". Slow to react. Trust prompt: `enter`. |
| `pi` | Never asks and has no sandbox, so its brief is its only limit. No trust prompt in a new folder. It shows `idle` before its first turn, so a wait sent right after launch returns at once: wait again. So far it has only led one worker in a trial, not a build. |
| `muse` | Worker only: its sandbox blocks `hc run` and `hc send`. Trust prompt: `enter`. It answers in its chat and ends its turn. |
| `opencode` | Status is unreliable in both directions; read the screen and check the file. With no permission block it asks for nothing. |

- **Read every screen right after launch.** Trust prompts are not reported as blocked. Accept
  trust for the work folder only.
- **Beta reads the workers' screens itself at three and five minutes.** A worker stuck reasoning
  never changes status, so nothing wakes its parent.
- **Save a worker's screen before killing one that wrote nothing:**
  `hc read NAME --lines 0 > .team/stall-NAME.txt`.
- **After each approval, read the screens of every blocked child.** A child that goes from one
  prompt straight to the next does not wake `hc wait`.
- **A missing part means the result is incomplete.** Reassign it or report it as missing; never
  report a partial result as the answer.
- **Beta keeps a timestamped progress log** (`.team/progress.log`), one line per event. Alpha
  follows the whole build from that file and `hc ls`.
- **Each level cleans up its own terminals,** and only those.

## Collecting results

```sh
hc wait --children any --timeout 60   # the next child's news
hc read NAME --lines 0                # its screen
hc send NAME 'Recheck the fix'
hc kill NAME; hc rm NAME
```

A report arrives as your next input, tagged `<hc from="t7 name">...</hc>`. `blocked` means the
agent is asking for a permission: read its screen and decide.
