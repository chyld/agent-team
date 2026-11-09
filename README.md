# Agent team

**alpha** is the primary agent; it writes and builds, and delegates review work to **beta**.

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

Each subagent is one shell command: harness, model, reasoning level, prompt. The command prints the
answer to stdout and exits.

## How to call each harness

Replace `MODEL` with a model from the roster and `PROMPT` with the task.

| Harness | Command |
|---|---|
| `claude` | `claude -p "PROMPT" --model MODEL --effort high` |
| `codex` | `codex exec -m MODEL -c model_reasoning_effort='"high"' --skip-git-repo-check "PROMPT"` |
| `grok` | `grok -p "PROMPT" -m MODEL --effort high` |
| `muse` | `muse exec --model MODEL --effort high "PROMPT"` |
| `opencode` | `opencode run -m "MODEL#high" "PROMPT"` |
| `agy` | `agy -p "PROMPT" --model MODEL --effort high` |

## Where the reasoning level goes

- `claude`, `grok`, `muse`, `agy`: the `--effort high` flag.
- `codex`: a config override, `-c model_reasoning_effort='"high"'`.
- `opencode`: a suffix on the model, `provider/model#high`.
- Reasoning `default` in the roster means the model has no `high` setting: call it with the bare model id, no `#high`.

## Examples

```sh
claude -p "Review src/auth.py for bugs" --model claude-sonnet-5-5 --effort high
codex exec -m gpt-6.1-sol -c model_reasoning_effort='"high"' --skip-git-repo-check "Review src/auth.py for bugs"
grok -p "Review src/auth.py for bugs" -m grok-4.7 --effort high
muse exec --model muse-ember-1.0 --effort high "Review src/auth.py for bugs"
opencode run -m "opencode-go/kimi-k3.1-pro#high" "Review src/auth.py for bugs"
agy -p "Review src/auth.py for bugs" --model gemini-4-argon --effort high
```

## Notes

- Run the command from the directory the subagent should work in.
- To run several subagents at once, start each command in the background and collect their output.
- These commands use each harness's default permissions, so a subagent may be unable to edit files or run commands. Grant more only when the task needs it.
