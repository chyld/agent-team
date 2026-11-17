# Agent team

A team of AI agents run through `hc`. Run `hc --skill` before you start anyone.

| # | Level | Harness | Model | Reasoning | Free? |
|---|---|---|---|---|---|
| 0 | alpha | `claude` | `claude-fable-5-2` | high | no |
| 1 | beta | `claude` | `claude-opus-5-5` | high | no |
| 2 | gamma | `claude` | `claude-sonnet-5-5` | high | no |
| 3 | gamma | `claude` | `claude-haiku-5-5` | high | no |
| 4 | gamma | `codex` | `gpt-6.2-sol` | high | no |
| 5 | gamma | `codex` | `gpt-6.2-astra` | high | no |
| 6 | gamma | `grok` | `grok-4.7` | high | no |
| 7 | gamma | `agy` | `gemini-4-hydrogen` | high | no |
| 8 | gamma | `muse` | `muse-ember-1.0` | high | no |
| 9 | gamma | `muse` | `muse-wonder-1.0` | high | no |
| 10 | gamma | `opencode` | `openrouter/deepseek/deepseek-v4.1-flash-1017` | high | no |
| 11 | vercel | `opencode` | `vercel/zai/glm-5.3` | high | no |
| 12 | vercel | `opencode` | `vercel/zai/glm-5.3-flash` | high | no |
| 13 | vercel | `opencode` | `vercel/moonshotai/kimi-k3` | high | no |
| 14 | vercel | `opencode` | `vercel/moonshotai/kimi-k3.1-pro` | high | no |
| 15 | vercel | `opencode` | `vercel/deepseek/deepseek-v4.1-flash` | high | no |
| 16 | omega | `opencode` | `opencode-go/minimax-m3.1-flash` | high | no |
| 17 | omega | `opencode` | `opencode-go/glm-5.3-flash` | high | no |
| 18 | omega | `opencode` | `opencode-go/kimi-k3.1-pro` | high | no |
| 19 | omega | `opencode` | `opencode-go/hy4` | high | no |
| 20 | omega | `opencode` | `opencode/beam-free` | high | 🟢 yes |
| 21 | omega | `opencode` | `opencode/deepseek-v4.1-flash-free` | high | 🟢 yes |
| 22 | omega | `opencode` | `opencode/flint-40b-free` | high | 🟢 yes |
| 23 | omega | `opencode` | `opencode/glm-5.3-flash-free` | high | 🟢 yes |
| 24 | omega | `opencode` | `opencode/iceman-free` |  | 🟢 yes |
| 25 | omega | `opencode` | `opencode/inkling-2-small-free` | high | 🟢 yes |
| 26 | omega | `opencode` | `opencode/longcat-2.5-free` |  | 🟢 yes |
| 27 | omega | `opencode` | `opencode/mimo-v2.6-flash-free` |  | 🟢 yes |
| 28 | omega | `opencode` | `opencode/nemotron-3.5-lightning-free` |  | 🟢 yes |
| 29 | omega | `opencode` | `opencode/nemotron-3.5-super-vl-free` | high | 🟢 yes |
| 30 | omega | `opencode` | `opencode/minimax-m3.1-flash-free` | high | 🟢 yes |
| 31 | omega | `opencode` | `openrouter/baidu/ernie-5.5-flash-preview:free` |  | 🟢 yes |

Agent 0 is alpha, agent 1 is beta, agents 2 to 10 are gamma, agents 11 to 15 are vercel, and agents 16 to 31 are the omega pool.
A blank reasoning cell means the model's default.

## Hierarchy

**The user decides the hierarchy.** Before a build, alpha asks the user which agents take part, at
which level, and who reports to whom, and starts no one until the user has answered. The levels in
the table are the arrangement used so far:

- **Alpha** takes the task from the user, writes `SPEC.md` and beta's brief, and checks the result
  with its own acceptance tests, which the team never sees.
- **Beta** writes the shared types and each gamma agent's brief, deals shuffled omegas to each
  gamma agent, approves what gamma asks for, integrates, and reports to alpha. It logs events in
  `.team/progress.log`.
- **Gamma** agents own one module each and report to beta. They start four omegas at once, two
  racing on the code and two on the tests, keep the first file to arrive, run the tests and send
  corrections. They write nothing themselves unless an omega has failed twice.
- **Omegas** write exactly one file each and start no one.

Nobody skips a level. Each level kills and removes the terminals it started, and only those. A
missing part means the result is incomplete: reassign it or report it as missing.

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
| `muse` | `muse --model MODEL --effort high "PROMPT"` (its own sandbox is the limit; do not disable it) |
| `opencode` | `env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL#high","permission":{"edit":"allow","bash":{"*":"ask"},"webfetch":"deny"}}' opencode --standalone --prompt "PROMPT"` (may edit files, asks beta for every command) |

These flags grant `codex` and `agy` their routine `hc` commands. That grant is the user's
decision; agents never widen permissions on their own. `codex` then prompts for nothing, so say
"no network use" in its brief. `agy` also needs [`hooks/agy/`](hooks/agy) copied into the work
folder as `.agents/`, with its short name set in `hooks.json` and beta's terminal id in
`.team/parent-id`.

Omegas (`MODEL` is the id from the table; for `opencode`, add `#high` when the table lists high
reasoning):

```sh
# opencode: may write one file, asks for everything else
hc run --bg --name NAME --cwd "$PWD" -- env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL","permission":{"edit":{"*":"ask","ABS_PATH":"allow","REL_PATH":"allow","./REL_PATH":"allow"},"bash":{"*":"ask"},"webfetch":"deny"}}' opencode --standalone --prompt "TASK"

# pi: no prompts and no sandbox, so the task text is its only limit; check afterwards what it touched
hc run --bg --name NAME --cwd "$PWD" -- pi --model MODEL --thinking high "TASK"
```

## Briefs and tasks

An omega's task names its one file and the spec section, and says: read only the spec and the
shared types, start writing within a minute and finish in one go, run no commands, say `DONE`.
Test writers also get: at most 15 tests, the spec's own examples first.

A gamma agent's brief says:

- Who the agent reports to, as a literal terminal id (`hc send t3 '...'`), and no one else.
- Which agents it may start, with the exact launch commands.
- To run `hc --skill` first, one command per call, never chained, with `hc send` text in single
  quotes.
- To wait with `hc wait --children all --timeout 60`, then read each omega's screen
  (`hc read NAME --lines 0`) and check whether its file exists.
- To refuse an omega's request for anything but its one file.

Beta approves only the `hc` commands and test runs its gamma agents' briefs call for, once each,
never "always allow" and never `--force`.

## Things to watch for

| Harness | Behaviour |
|---|---|
| `claude` | Runs in auto mode: fastest, never asks, so its brief is its only limit. In a new folder it stops at a trust prompt that is not flagged: `hc keys NAME down enter`. |
| `codex` | Careful reviewer that invents requirements unless held to the one-pass, quote-the-spec rule. Trust prompt: `enter`. |
| `grok` | Queues every message until its turn ends, and reviews slowly. Give it no review and no report file; its report is one `hc send`. Still asks before `rm`, `mv` and redirects. |
| `agy` | Opens with a chained command that searches the home folder; refuse it and send "continue". Slow to react. Trust prompt: `enter`. |
| `pi` | Omega only. Never asks and has no sandbox, so its task is its only limit: check afterwards what it touched. No trust prompt in a new folder. It shows `idle` before its first turn, so a wait sent right after launch returns at once: wait again. It has not yet run as an omega in a build. |
| `muse` | Its sandbox blocks `hc run` and `hc send`, so as a gamma agent it can neither start omegas nor send its report: beta reads its screen. Trust prompt: `enter`. It answers in its chat and ends its turn. It has not yet run as a gamma agent in a build. |
| `opencode` | Status is unreliable in both directions; read the screen and check the file. With no permission block it asks for nothing. It has not yet run as a gamma agent in a build. |

- **Read every screen right after launch,** and again after each approval. Trust prompts are not
  reported as blocked, and a child that goes from one prompt straight to the next wakes no one.
  Accept trust for the work folder only.
- **An omega has stalled** when its file does not exist after three minutes (four for tests). Its
  status never changes, so its gamma agent reads the omegas' screens itself, kills the stalled one
  and starts a replacement that beta deals.
