# Agent team

Alpha leads, beta manages, gamma does the work with help, and delta and epsilon are the pool of
workers that gamma draws from. See [Chain of command](#chain-of-command).

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

## Chain of command

Work flows down one level at a time, and reports flow back up the same way.

```
alpha (0)
  └─ beta (1)
       └─ gamma (2-8), seven agents
            └─ two workers each, dealt at random from delta + epsilon (9-23)
```

- **Alpha delegates only to beta.** Alpha takes the task from the user, writes the brief for beta,
  waits for beta's report, checks it, and answers the user. Alpha never starts gamma or the workers.
- **Beta delegates only to gamma.** Beta splits the task into up to seven parts, starts one gamma
  agent per part, deals each one its workers, collects the gamma reports and combines them into
  one report for alpha.
- **Gamma delegates only to its own workers.** Each gamma agent starts the two workers beta dealt
  it, gives them pieces of its part, checks what comes back, and reports to beta.
- **Workers delegate to no one.** They do the piece they are given and answer.
- Nobody skips a level, in either direction. A worker reports to its gamma agent, never to beta
  or alpha.

### Dealing the workers

Delta and epsilon are one pool of 15 workers. They no longer act as teams of their own.

- **Each gamma agent gets two workers.** Seven gamma agents take 14 of the 15, so every gamma
  agent has the same number.
- **One worker sits out each round.** Fifteen does not divide by seven. The one left over is
  whichever comes last in the shuffle, so it changes from round to round.
- **Beta shuffles the pool every time it hands out workers.** A new round of gamma work means a
  new shuffle: no gamma agent keeps its workers from the last round, and no worker is given to two
  gamma agents in the same round.
- **If beta starts fewer than seven gamma agents,** each still gets two, and the rest of the pool
  sits out.

Beta deals with this. It prints one line per gamma agent with its two workers:

```sh
pool=(
  'openrouter/deepseek/deepseek-v4.1-flash-1017#high'
  'opencode-go/minimax-m3.1-flash#high'
  'opencode-go/glm-5.3-flash#high'
  'opencode-go/kimi-k3.1-pro#high'
  'opencode-go/hy4#high'
  'opencode/beam-free#high'
  'opencode/deepseek-v4.1-flash-free#high'
  'opencode/flint-40b-free#high'
  'opencode/glm-5.3-flash-free#high'
  'opencode/iceman-free'
  'opencode/inkling-2-small-free#high'
  'opencode/longcat-2.5-free'
  'opencode/mimo-v2.6-flash-free'
  'opencode/nemotron-3.5-lightning-free'
  'opencode/nemotron-3.5-super-vl-free#high'
)
gamma=(sonnet haiku sol terra grok muse argon)
mapfile -t deal < <(printf '%s\n' "${pool[@]}" | shuf)
for i in "${!gamma[@]}"; do
  echo "${gamma[i]}: ${deal[2*i]} ${deal[2*i+1]}"
done
echo "sits out: ${deal[14]}"
```

Beta writes each gamma agent's two workers into that agent's brief, as the exact model strings
above. The `#high` suffix is already there for the models that have it.

### What each level's brief must say

- Who the agent reports to, as a literal terminal id, and that it reports to no one else.
- Which agents it may start, by name and model, and that it starts no others.
- To read `hc --skill` first.
- To kill and remove the terminals it started before it reports.
- What it may approve when one of its children is blocked. The safe default is nothing: report it
  upward.

### Not yet tested

- Only two levels have been run: an agent starting agents that start nothing. This structure has
  three levels below alpha.
- Only a `claude` agent has been tried as a middle agent. `codex`, `grok`, `muse` and `agy` in
  gamma have to run `hc run`, `hc wait`, `hc read` and `hc send` themselves. Their default
  permissions ask before shell commands, and `muse`'s sandbox has refused `hc send`, so expect
  beta to be approving prompts for them, or to grant them the `hc` commands at launch.

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

## Nested agents

A subagent can start subagents of its own. Tested with Sonnet 5.5 starting the five delta agents,
asking each a math question, and reporting back: it worked, with all five answers collected.

- **Say so explicitly.** A subagent must not start agents unless its task assigns that. Name the
  agents it may start, and tell it to start no others.
- **Give it a brief file.** The middle agent needs more than one line: which agents to start, the
  exact launch command, how to collect, how to clean up and how to report. Put that in a file and
  make its task `Read brief.md in this folder and follow it exactly.`
- **Tell it to read the hc skill first,** the same as you did: `hc --skill`.
- **Its children are its own.** They are children of the middle agent, not of you. They end when it
  ends, `hc wait --children` in your terminal does not see them, and you wait only on the middle
  agent. `hc ls` still lists every terminal, with its parent.
- **Write your terminal id into the brief as a literal,** e.g. `hc send t3 "done"`. In a brief file
  nothing expands `$HC_TERMINAL_ID`, and inside the middle agent it would be that agent's own id.
- **Do not trust status alone for `opencode` agents.** `hc wait --children all` returned at once
  with every child `idle` before two of them had answered, and in other runs a finished agent
  stayed `working`. Tell the middle agent to read each screen with `hc read NAME --lines 0`, and to
  wait again if an answer is not there yet.
- **Each level cleans up its own.** The middle agent kills and removes the terminals it started
  before it reports. You then kill and remove the middle agent.
- **Permission prompts stop at the middle agent.** A blocked grandchild notifies its parent, not
  you. Say in the brief what the middle agent may approve; the safe default is to approve nothing
  and report it.

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
