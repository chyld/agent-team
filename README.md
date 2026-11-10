# Agent team

Alpha leads, beta manages, the six gamma agents do the work with help, and delta and epsilon are
the pool of 16 workers that gamma draws from. See [Chain of command](#chain-of-command).

| # | Team | Harness | Model | Reasoning |
|---|---|---|---|---|
| 0 | alpha | `claude` | `claude-fable-5-2` | high |
| 1 | beta | `claude` | `claude-opus-5-5` | high |
| 2 | gamma | `claude` | `claude-sonnet-5-5` | high |
| 3 | gamma | `claude` | `claude-haiku-5-5` | high |
| 4 | gamma | `codex` | `gpt-6.1-sol` | high |
| 5 | gamma | `codex` | `gpt-6.1-terra` | high |
| 6 | gamma | `grok` | `grok-4.7` | high |
| 7 | gamma | `agy` | `gemini-4-argon` | high |
| 8 | delta | `muse` | `muse-ember-1.0` | high |
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
       └─ gamma (2-7), six agents
            └─ two workers each, dealt at random from delta + epsilon (8-23)
```

- **Alpha delegates only to beta.** Alpha takes the task from the user, writes the brief for beta,
  waits for beta's report, checks it, and answers the user. Alpha never starts gamma or the workers.
- **Beta delegates only to gamma.** Beta splits the task into up to six parts, starts one gamma
  agent per part, deals each one its workers, collects the gamma reports and combines them into
  one report for alpha.
- **Gamma delegates only to its own workers.** Each gamma agent starts the two workers beta dealt
  it, gives them pieces of its part, checks what comes back, and reports to beta.
- **Workers delegate to no one.** They do the piece they are given and answer.
- Nobody skips a level, in either direction. A worker reports to its gamma agent, never to beta
  or alpha.

### Dealing the workers

Delta and epsilon are one pool of 16 workers: 15 `opencode` models and `muse`. They no longer act
as teams of their own.

- **Each gamma agent gets two workers.** Six gamma agents take 12 of the 16, so every gamma agent
  has the same number.
- **Four workers sit out each round.** Sixteen does not divide by six. The four left over are
  whichever come last in the shuffle, so they change from round to round.
- **Beta shuffles the pool every time it hands out workers.** A new round of gamma work means a
  new shuffle: no gamma agent keeps its workers from the last round, and no worker is given to two
  gamma agents in the same round.
- **If beta starts fewer than six gamma agents,** each still gets two, and the rest of the pool
  sits out.
- **The workers sitting out are the reserve.** If a worker fails, its gamma agent reports that to
  beta, and beta hands it one from the reserve.

Beta deals with this. Each pool entry is a harness and a model. It prints one line per gamma agent
with its two workers:

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
)
gamma=(sonnet haiku sol terra grok argon)
mapfile -t deal < <(printf '%s\n' "${pool[@]}" | shuf)
for i in "${!gamma[@]}"; do
  echo "${gamma[i]}: [${deal[2*i]}] [${deal[2*i+1]}]"
done
printf 'sits out: [%s]\n' "${deal[@]:12}"
```

Beta writes each gamma agent's two workers into that agent's brief, as the exact harness and
model above. The `#high` suffix is already there for the `opencode` models that have it.

### Muse as a worker

`muse` was a gamma agent until the full-chain test showed its sandbox cannot run `hc run` or
`hc send`. A worker needs neither, so it is now in the pool. A gamma agent that is dealt `muse`
handles it differently from the `opencode` workers:

- **Launch:** `hc run --bg --name NAME --cwd "$PWD" -- muse --model muse-ember-1.0 --effort high "PROMPT"`.
  There is no `OPENCODE_CONFIG_CONTENT` and no `#high`; its own sandbox is its permission limit.
  Do not disable it.
- **Trust prompt:** in a folder it has not seen, `muse` stops at a folder-trust prompt that is not
  flagged as blocked. Read its screen right after launch and accept with `hc keys NAME enter`,
  for the work folder only.
- **Result:** it cannot `hc send`. Tell it to answer in its chat and end its turn. It reports its
  own `done` status, which `hc wait --children` picks up; then read its screen.

### What each level's brief must say

- Who the agent reports to, as a literal terminal id, and that it reports to no one else.
- Which agents it may start, by name and model, and that it starts no others.
- To read `hc --skill` first.
- To kill and remove the terminals it started before it reports.
- What it may approve when one of its children is blocked. The safe default is nothing: report it
  upward.

### Tested: the full chain

**Round 3, with `muse` forced into the deal,** run on 2026-11-09 with "what is 2¹ + 2² + ... +
2¹²?":

- **The chain's answer was 8190, which is correct.** All six parts and all twelve worker answers
  were right, first time.
- **`muse` works as a worker.** The shuffle left it in the reserve, so beta swapped it with a
  randomly chosen dealt worker. Its gamma agent (`agy`) launched it with the command in
  [Muse as a worker](#muse-as-a-worker), it answered in seconds, reported its own `done` status,
  and was read off its screen, then killed and removed. `muse` raised no prompt of its own.
- **Its folder-trust prompt is still untested.** None appeared, most likely because `muse` already
  trusted the test folder from round 1.
- It took about seven and a half minutes, with 34 approvals by beta and none refused.

**Round 2, the current structure** (six gamma agents, 16 workers), run on 2026-11-09 with "what
is 1³ + 2³ + ... + 12³?":

- **The chain's answer was 6084, which is correct.** All six gamma agents delivered, all twelve
  worker answers were right, nothing was reassigned and the reserve was not used.
- It took about six minutes, again almost all of it approvals: 30 by beta, none refused.
- `muse` was dealt into the reserve, so it was not exercised until round 3.

**Round 1, the earlier structure,** with `muse` as a seventh gamma agent and 15 workers, run the
same day with the question "what is 1² + 2² + ... + 14²?". Alpha briefed beta, beta
split it across the seven gamma agents and dealt the workers, each gamma agent asked its two
workers for one square each and added them, and beta added the sums.

- **Six of seven gamma agents delivered,** all correct, and every worker answer was correct.
- **The chain's total was 750, not 1015.** `muse` could not start its workers, so 11² + 12² never
  came back. Beta reported the total as incomplete and named the missing part.
- It took about six minutes for a trivial question. Nearly all of that was beta approving
  permission prompts: 18 approvals and two refusals.
- Alpha saw only beta. No prompt or report from gamma or the workers reached alpha.
- Every level cleaned up its own terminals.

### Known issues, by harness as a gamma agent

| Harness | Can it run workers? | What happens |
|---|---|---|
| `claude` | yes | No prompts, done in under a minute. |
| `grok` | yes | `--allow 'Bash(hc:*)'` is unreliable. It asked for chained commands in round 1 and for two plain, long `hc run` commands in round 2. About two approvals a round. |
| `codex` | yes, slowly | Its sandbox cannot reach the hc core, so it asks before every `hc` command except `hc --skill`: seven to ten approvals per agent. |
| `agy` | yes, slowly | Asks before every command and file read: about eight approvals. Refusing a command ends its turn, so it then needs an `hc send` to carry on. |
| `muse` | **no** | Its sandbox blocks `hc run` (`cannot start core: Read-only file system`) and `hc send`. It can read `hc --skill` and nothing more. |

### Rules that came out of the test

- **`muse` cannot manage workers, so it moved to the worker pool.** See
  [Muse as a worker](#muse-as-a-worker). Do not disable its sandbox to get round this.
- **A missing part means the answer is incomplete.** When a gamma agent fails, beta gives that
  part to a gamma agent that has finished, together with the failed agent's two workers, and
  only reports a total once every part is in. If it cannot, it reports the answer as incomplete
  and names what is missing. It never reports a partial total as the answer.
- **Tell `grok` to run one `hc` command per call,** never chained with `&&` or `;`.
- **Put `hc --skill` on the list of what a parent may approve.** Every brief requires it, so a
  parent told to approve only `hc run`, `wait`, `read`, `kill`, `rm` and `send` has to refuse it.
- **Say what a refused agent should do next.** For `agy`, a refusal stops the turn. The parent
  follows a refusal with `hc send NAME "skip that step and continue with your brief"`.
- **Read every screen right after launch.** Folder-trust prompts from `muse` and `agy` were not
  flagged as blocked. Accept trust only for the folder the work is in.
- **After each approval, read the screens of every blocked child.** `hc wait --children any` does
  not wake when a child goes from one prompt straight to the next, because its status never
  changes. In round 2 a prompt sat for a minute this way.
- **Budget for approvals.** With default permissions, `codex` and `agy` gamma agents each cost
  their parent ten to twelve approvals a round. To cut that, the user has to decide to grant those
  harnesses the `hc` commands at launch; an agent must not widen permissions on its own.

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
  you: in the full-chain test beta handled 20 prompts and alpha saw none. Say in the brief exactly
  which commands the middle agent may approve, once each, and that it reports anything else.

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
