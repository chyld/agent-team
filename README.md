# Agent team

| # | Team | Harness | Model | Reasoning |
|---|---|---|---|---|
| 0 | alpha | `claude` | `claude-fable-5-2` | high |
| 1 | beta | `claude` | `claude-opus-5-5` | high |
| 2 | gamma | `claude` | `claude-sonnet-5-5` | high |
| 3 | gamma | `claude` | `claude-haiku-5-5` | high |
| 4 | gamma | `codex` | `gpt-6.1-sol` | high |
| 5 | gamma | `codex` | `gpt-6.1-terra` | high |
| 6 | gamma | `grok` | `grok-4.7` | high |
| 7 | gamma | `muse` | `muse-ember-1.0` | high |
| 8 | gamma | `agy` | `gemini-4-argon` | high |
| 9 | delta | `opencode` | `openrouter/deepseek/deepseek-v4.1-flash-1017` | high |
| 10 | delta | `opencode` | `opencode-go/minimax-m3.1-flash` | high |
| 11 | delta | `opencode` | `opencode-go/glm-5.3-flash` | high |
| 12 | delta | `opencode` | `opencode-go/kimi-k3.1-pro` | high |
| 13 | delta | `opencode` | `opencode-go/hy4` | high |
| 14 | epsilon | `opencode` | `opencode/beam-free` | high |
| 15 | epsilon | `opencode` | `opencode/deepseek-v4.1-flash-free` | high |
| 16 | epsilon | `opencode` | `opencode/flint-40b-free` | high |
| 17 | epsilon | `opencode` | `opencode/glm-5.3-flash-free` | high |
| 18 | epsilon | `opencode` | `opencode/iceman-free` | default |
| 19 | epsilon | `opencode` | `opencode/inkling-2-small-free` | high |
| 20 | epsilon | `opencode` | `opencode/longcat-2.5-free` | default |
| 21 | epsilon | `opencode` | `opencode/mimo-v2.6-flash-free` | default |
| 22 | epsilon | `opencode` | `opencode/nemotron-3.5-lightning-free` | default |
| 23 | epsilon | `opencode` | `opencode/nemotron-3.5-super-vl-free` | high |

**Read the hc skill first:** run `hc --skill` and read it before you start anyone. It is the manual
for everything below.

Each subagent is one `hc run` command: a name, a harness, a model, a reasoning level and a prompt. It
starts the harness interactively in its own herdr-core terminal, as a child of yours, so it stays
watchable and steerable. Never use a one-shot mode (`claude -p`, `grok -p`, `agy -p`, `codex exec`,
`muse exec`, `opencode run`).

## How to call each harness

Every call has the same wrapper:

```sh
hc run --bg --name NAME --cwd DIR -- HARNESS_COMMAND
```

Replace `NAME` with a unique terminal name (1-32 characters from `a-z 0-9 - _`, so no model ids),
`DIR` with the folder the subagent should work in, `MODEL` with a model from the roster and `PROMPT`
with the task.

| Harness | `HARNESS_COMMAND` |
|---|---|
| `claude` | `claude --model MODEL --effort high "PROMPT"` |
| `codex` | `codex --no-daemon -m MODEL -c model_reasoning_effort='"high"' "PROMPT"` |
| `grok` | `grok -m MODEL --effort high "PROMPT"` |
| `muse` | `muse --model MODEL --effort high "PROMPT"` |
| `opencode` | `env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL#high"}' opencode --standalone --prompt "PROMPT"` |
| `agy` | `agy --model MODEL --effort high -i "PROMPT"` |

- `codex` needs `--no-daemon`, or its commands run outside hc.
- `opencode`'s interactive mode has no `-m` flag, so the model goes in `OPENCODE_CONFIG_CONTENT`.
- `agy` needs `-i` to take a first prompt and stay interactive.

## Where the reasoning level goes

- `claude`, `grok`, `muse`, `agy`: the `--effort high` flag.
- `codex`: a config override, `-c model_reasoning_effort='"high"'`.
- `opencode`: a suffix on the model, `provider/model#high`.
- Reasoning `default` in the roster means the model has no `high` setting: call it with the bare model id, no `#high`.

## The prompt

- Put the task in the launch command. A message sent while the harness boots can be dropped.
- End it with how to report: `Report with hc send $HC_TERMINAL_ID when done or stuck.` Inside double
  quotes your shell fills in your own terminal id at launch, which is what the subagent needs.
- `muse`'s sandbox blocks `hc send`. Tell it to write its output file and end its turn instead.
- Say what is off limits, e.g. `Read-only; no subagents.`

## Examples

```sh
hc run --bg --name sonnet --cwd ~/app -- claude --model claude-sonnet-5-5 --effort high "Review src/auth.py for bugs. Read-only; no subagents. Report with hc send $HC_TERMINAL_ID when done or stuck."
hc run --bg --name sol --cwd ~/app -- codex --no-daemon -m gpt-6.1-sol -c model_reasoning_effort='"high"' "Review src/auth.py for bugs. Read-only; no subagents. Report with hc send $HC_TERMINAL_ID when done or stuck."
hc run --bg --name grok --cwd ~/app -- grok -m grok-4.7 --effort high "Review src/auth.py for bugs. Read-only; no subagents. Report with hc send $HC_TERMINAL_ID when done or stuck."
hc run --bg --name muse --cwd ~/app -- muse --model muse-ember-1.0 --effort high "Review src/auth.py for bugs. Read-only; no subagents. Write findings to /tmp/muse-review.md and end your turn."
hc run --bg --name kimi --cwd ~/app -- env 'OPENCODE_CONFIG_CONTENT={"model":"opencode-go/kimi-k3.1-pro#high"}' opencode --standalone --prompt "Review src/auth.py for bugs. Read-only; no subagents. Report with hc send $HC_TERMINAL_ID when done or stuck."
hc run --bg --name argon --cwd ~/app -- agy --model gemini-4-argon --effort high -i "Review src/auth.py for bugs. Read-only; no subagents. Report with hc send $HC_TERMINAL_ID when done or stuck."
```

## Collecting results

```sh
hc wait --children any      # the next child's news: done, blocked, a message, an exit
hc read sonnet --lines 100  # its screen and history
hc send sonnet "Recheck the fix"
hc kill sonnet; hc rm sonnet
```

- A report arrives as your next input, tagged `<hc from="t7 sonnet">...</hc>`.
- Never sleep or poll. Wait with `hc wait`.
- `blocked` means the subagent is asking for a permission: read its screen with
  `hc read NAME --lines 0` and decide. Never `--force` past it.
- When you have the results, kill and remove every terminal you started, and only those.

## Notes

- To run several subagents at once, start each one with its own `--name`; `--bg` returns at once.
- These commands use each harness's default permissions. Most harnesses then ask before edits and
  shell commands, which shows up as `blocked`. Grant more only when the task needs it.
- `opencode` is the exception: with no permission block it asks for nothing. Add one to
  `OPENCODE_CONFIG_CONTENT`, next to the model. This one asks before every edit and every shell
  command except `hc send`, and denies web fetches:

  ```json
  {"model":"MODEL#high","permission":{"edit":{"*":"ask"},"bash":{"*":"ask","hc send *":"allow"},"webfetch":"deny"}}
  ```
