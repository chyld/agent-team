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
- **Four in reserve is not enough for a build.** The second build had seven stalls and used up
  the reserve in five minutes. When it is empty, beta may hand a gamma agent a worker that has
  already finished its job for another gamma agent and been removed. No worker does two jobs at
  once.
- **The workers sitting out are the reserve.** When a worker fails or stalls, beta hands its gamma
  agent one from the reserve. Beta writes the replacement's exact launch command into a file and
  tells the gamma agent with `hc send` to kill the old worker and follow the file. A long command
  sent in a message can be cut off; a file is not.

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
  for the work folder only. This was confirmed in the build test.
- **Result:** it cannot `hc send`. Tell it to answer in its chat and end its turn. It reports its
  own `done` status, which `hc wait --children` picks up; then read its screen.

### Giving workers real work

In the build test each gamma agent owned one module. One worker wrote the code and the other wrote
the tests, both from the same section of the spec, and the gamma agent ran the tests and reviewed.

- **A worker writes exactly one file.** For `opencode`, allow that file in the permission block,
  as an absolute and a relative path, and leave everything else on `ask`:

  ```sh
  hc run --bg --name NAME --cwd "$PWD" -- env 'OPENCODE_CONFIG_CONTENT={"model":"MODEL","permission":{"edit":{"*":"ask","ABS_PATH":"allow","REL_PATH":"allow"},"bash":{"*":"ask"},"webfetch":"deny"}}' opencode --standalone --prompt "TASK"
  ```

  No worker wrote outside its file.
- **The task says:** read the named spec section and the shared types, write the one file, run no
  commands, start no agents, and say `DONE` in the chat. Workers do not `hc send`; the gamma agent
  reads their screens and checks that the file exists.
- **A worker blocked on anything but its one file is rejected,** and told with `hc send` to write
  only its file. One model kept asking for `ls` and `find` and never wrote anything; replace a
  worker that does this.
- **The gamma agent does not write the files.** It runs the tests, reads both files, and sends a
  precise correction to the worker that got it wrong. Only after two failed rounds does it edit a
  file itself. In the build test one round was always enough and nothing was edited by hand.
- **Have the gamma agent read the code after the tests pass.** The only real bug in a module was
  one its tests did not catch; the gamma agent found it by reading.
- **Have it check only what the spec states.** In the second build a `codex` agent's read-through
  tightened a module beyond the spec, broke a case that had worked, and needed a second round to
  undo it. Say "do not add requirements the spec does not state" in the brief, and have beta
  refuse corrections that do.
- **Code is easy for the workers; tests are a coin toss.** Over two builds, 12 of 13 code workers
  delivered a correct module, most in under a minute, free models included. Test writers stalled
  about half the time: 3 of 6 in the first build and 6 of 11 attempts in the second.
- **No model is reliably a good test writer.** After the first build this README listed four
  models that "wrote tests well" and the second build gave them the tests. Three of the four
  stalled, and the fourth wrote one test file in 97 seconds and stalled on the next. Do not pick
  test writers from a list. Plan for half of them to fail and replace them quickly.

  | Model | As test writer, build 1 | Build 2 |
  |---|---|---|
  | `muse` | not used | delivered twice, about a minute each |
  | `opencode-go/minimax-m3.1-flash` | delivered, with wrong expected values | delivered |
  | `opencode/inkling-2-small-free`, `opencode/iceman-free` | not used | delivered |
  | `opencode/nemotron-3.5-super-vl-free` | delivered | delivered once, stalled once |
  | `opencode-go/hy4`, `opencode-go/glm-5.3-flash`, `opencode/mimo-v2.6-flash-free` | delivered | stalled |
  | `opencode/flint-40b-free`, `opencode/nemotron-3.5-lightning-free`, `opencode/glm-5.3-flash-free` | produced nothing | given code instead: one delivered, one stalled, one tried to write in another folder |
  | `opencode/longcat-2.5-free` | not used | stalled |
- **Quote `hc send` text in single quotes.** In double quotes the shell turned `$1.00` in a
  correction into `.00`.
- **Modules that depend on each other land at the same time.** Tell each gamma agent to code
  against the spec's signatures and to keep its tests independent of the other modules, with
  small stand-ins. The lead writes the shared types before launching anyone.

### Fixing test-writer stalls

In three builds test writers stalled about half the time, on every model. Saved screens showed
what a stall is: the worker reads the spec, then sits in one unbroken stretch of reasoning and
never starts writing. It is not at a prompt and not looping on tools. Two changes took stalls from
4 in 10 attempts to 0 in 12.

- **Make the test task small and say so.** This did most of the work. The task that worked:

  > Write `tests/test_MODULE.py` for the MODULE section of `SPEC.md`. Use `unittest`. Write at
  > most 15 tests: first every example the spec states, with the exact values the spec gives, then
  > one or two simple cases per function. Do not work out long expected strings by hand: when the
  > spec gives no exact output, assert on something simple (a length, a prefix, a type, an
  > exception). Do not plan at length. Write the file within two minutes, in one go; a short
  > correct file now is worth more than a thorough one later. If importing another module fails
  > for any reason (`except Exception`), use a small stand-in.

- **Race two test writers on every module.** Each gamma agent starts three workers at once: the
  code worker, the test worker, and a second test writer on the code worker's model, writing
  `tests/test_MODULE_alt.py`. The gamma agent uses whichever file arrives first, keeps the second
  if it also passes, and deletes it without a correction round if it fails. With no stalls the
  race never had to rescue a module, but it saved a correction round where the first file was
  wrong. It costs six more workers.
- **Give code workers the same "do not plan at length" line.** They did not get it in round 7, and
  the only stall was a code worker reasoning for three minutes.
- **Save a stalled worker's screen before killing it,** with
  `hc read NAME --lines 0 > .team/stall-NAME.txt`. That is how the cause was found.
- **Apply "asks a second time means stalled" only before a worker has delivered.** Workers that
  kept asking to run commands after writing their file caused a false stall report.

### Fixing code-writer stalls

- **Give code writers the "write now" line too:** "Do not plan at length: start writing within
  one minute and finish within two, in one go."
- **Race two code writers on every module.** Each gamma agent starts four workers at once: code
  (`tally/MODULE.py`), tests, a second test writer on the code worker's model, and a second code
  writer on the test worker's model writing `tally/MODULE_alt.py`. Whichever module file exists
  first is used. If it is the `_alt` file, the gamma agent kills the first code worker and then
  moves the file into place; always kill before moving. No `_alt` module file is left at the end.
- **A race replaces the stall rule for the first minutes.** Nobody has to notice anything or ask
  beta for a replacement; the slow worker is simply killed when the fast one delivers.
- **Have the gamma agent save a loser's screen before killing it.** The race kills non-deliverers
  at about a minute, before beta's three-minute watch sees them.
- **Limit the read-through:** one pass, at most one correction message, and every point must quote
  the sentence of the spec the code breaks. This stopped `codex` inventing requirements. Add a
  time limit of two minutes as well; `grok` spent four.
- **The test race can probably go.** No test writer stalled in rounds 7 or 8, so the smaller task
  was enough, and the race costs six workers. The code race earned its place.
- **Open problems:** one `opencode` worker was asked to approve a write to its own allowed file,
  probably a path spelled differently from the two allowed forms; and `agy` prompted for
  `rm tally/MODULE_alt.py` although its allow-list and hook cover it.

### Managing a grok agent

`grok` launches and watches workers well, but reviews slowly and queues every message sent to it
until its turn ends.

- **It does no read-through.** Its job ends when the module and one test file pass. Beta reads its
  module against the spec while the other agents finish. In round 9 this cut its module from over
  nine minutes to under five.
- **It writes no report file.** Its report is one short `hc send`, and beta writes the file. Its
  own report file needed an approval in every round before.
- **Send it nothing while it is working.** If beta must, it sends, reads grok's screen, and if the
  message shows as queued while grok sits at its input, presses `hc keys NAME enter`.
- It still asks before `rm`, `mv` and a redirect, whatever its flags: two approvals in round 9.
- **The same treatment would suit `agy`,** which is now the slowest manager for the same reason:
  its workers are done in two minutes and it then spends five reacting.

### Wording for a race

- Tell the second writer "write only `tally/MODULE_alt.py`; it is renamed later; do not write
  `tally/MODULE.py`". Saying the file "must be importable as `tally.MODULE`" made a worker try to
  write the other racer's file.
- Tell every worker that the folders it writes into already exist. One sat at a prompt for
  `mkdir -p tests`.
- Allow three spellings of the worker's file in the `opencode` permission block: absolute,
  relative, and relative with `./` in front.

### Watching for stalled workers

A worker stuck "thinking" never changes status, so nothing wakes its parent's `hc wait`. In the
build test three workers sat silent for eight minutes and no gamma agent noticed. The rule "tell
beta if a worker has produced nothing after five minutes" did not work, because the gamma agents
were asleep in their waits.

- **Gamma agents wait with a timeout,** `hc wait --children all --timeout 60`, and after each
  wait read each worker's screen and check whether its file exists. A worker with no file three
  minutes after launch is reported to beta as stalled.
- **Beta checks the workers' screens itself at three and five minutes.** This is the one place a
  level looks past the level below it. Beta only reads; it still acts through the gamma agent.
- **This worked in the second build.** Five of seven stalls were reported by the gamma agent
  itself within three to four minutes, against eight minutes and nobody in the first. Beta's own
  watch caught the other two first, including a worker trying to write in another project's
  folder. No worker killed at three minutes showed any sign it would have delivered.
- **It costs approvals.** Each one-minute cycle is a wait, two screen reads and a file check. For
  a `codex` or `agy` gamma agent that is two to four approvals a minute from beta.
- **`grok` queues incoming messages until its turn ends,** including hc's notices about its own
  workers. It reacts late, so do not rely on it to catch a stall.

### What each level's brief must say

- Who the agent reports to, as a literal terminal id, and that it reports to no one else.
- Which agents it may start, by name and model, and that it starts no others.
- To read `hc --skill` first.
- To kill and remove the terminals it started before it reports.
- What it may approve when one of its children is blocked. The safe default is nothing: report it
  upward.

### Tested: the full chain

**Round 9, the same build with the grok fixes,** run on 2026-11-09. Changes: the `grok` agent
did no read-through and wrote no report file, beta reviewed its module instead, and every agent's
read-through got a two-minute limit; see [Managing a grok agent](#managing-a-grok-agent).

| | Round 8 | Round 9 |
|---|---|---|
| Result | 173 tests, 24 of 24 acceptance tests | 105 tests, 24 of 24 acceptance tests |
| Time, beta start to report | about 13 minutes | about 11 minutes |
| `grok`'s module, launch to report | 9m20s | about 4m35s |
| Slowest module | 9m20s, `grok` | 7m23s, `agy` |
| Approvals by beta | 3, and 1 refusal | 2, and 1 refusal |

- **`grok` is no longer the slow one.** Its module and tests were on disk 96 seconds after
  launch, and beta's own review of the module was finished before `grok`'s report arrived. That
  review found one real edge case, which beta fixed at integration.
- **`codex` reviews took seconds** under the one-pass, two-minute rule, and listed their doubts
  for beta instead of chasing them.
- **The slow part moved to `agy`.** All four of its workers' files were on disk two minutes after
  launch; the other five minutes were `agy` itself: a refused opening command, long pauses, one
  real correction and a read-through that found nothing.
- **The code race rescued one module** whose first writer was still reasoning when the second
  delivered at 42 seconds.
- **Workers in a race tried to write the other racer's file** three times. The one-file permission
  blocks stopped all three. The task wording caused it; see below.
- **Across the six builds:** 22, 23, 16, 15, 13 and 11 minutes.

**Round 8, the same build with the code-writer fixes,** run on 2026-11-09. Changes: code
writers got the "write now" line, two code writers raced on every module, and the read-through
was limited to one pass whose every point must quote the spec; see
[Fixing code-writer stalls](#fixing-code-writer-stalls).

| | Round 7 | Round 8 |
|---|---|---|
| Result | 144 tests, 24 of 24 acceptance tests | 173 tests, 24 of 24 acceptance tests |
| Time, beta start to report | about 15 minutes | about 13 minutes |
| Workers that stalled a module | 1 | 0 |
| Slowest module | 10m40s, a stalled code writer | 9m20s, `grok`'s read-through |
| Approvals by beta | 1, and 2 refusals | 3, and 1 refusal |

- **No module stalled.** Ten of twelve code writers delivered within 54 seconds. The second code
  writer won the race in three of six modules, and in one of them the first was stuck at a
  permission prompt and would have been a three-minute stall.
- **`codex` stayed inside the spec.** With the one-pass rule both `codex` agents finished in two
  to four and a half minutes and sent no beyond-spec corrections.
- **The slow part moved to `grok`.** Its module and tests were on disk two minutes after launch;
  it then spent four minutes on its read-through, and beta's message overruling it sat in grok's
  queue for over a minute. Five modules were done within five minutes of launch.
- **Across the five builds:** 22, 23, 16, 15 and 13 minutes, and 75, 102, 3, 1 and 3 approvals.

**Round 7, the same build with the test-writer fixes,** run on 2026-11-09. Two changes: the
smaller test task, and two test writers racing on every module; see
[Fixing test-writer stalls](#fixing-test-writer-stalls).

| | Round 6 | Round 7 |
|---|---|---|
| Result | 281 tests, 24 of 24 acceptance tests | 144 tests, 24 of 24 acceptance tests |
| Time, beta start to report | about 16 minutes | about 15 minutes |
| Test writers that stalled | 4 of 10 attempts | 0 of 12 |
| Workers that stalled | 4 | 1, a code writer |
| Approvals by beta | 3, and 1 refusal | 1, and 2 refusals |

- **No test writer stalled.** Most delivered in 26 to 46 seconds, including on `report` and
  `budget`, where they had stalled in every earlier build. Nine of twelve test files passed as
  written.
- **The build was only a minute faster,** because the one stall, a code writer on the `agy`
  agent's module, set the time: replaced at 3m20s, and the replacement took 3m05s. The other five
  modules were done within seven minutes of launch.
- **Fewer tests, same result.** The team wrote 144 tests against 281, and the hidden acceptance
  tests passed either way.

**Round 6, the same build with launch grants,** run on 2026-11-09. The user decided to grant
`codex` and `agy` their routine `hc` commands at launch; see
[Granting gamma agents their hc commands](#granting-gamma-agents-their-hc-commands). Nothing else
changed except that test writers were no longer picked from a list and finished workers could be
re-used as replacements.

| | Round 5 | Round 6 |
|---|---|---|
| Result | 239 tests, 24 of 24 acceptance tests | 281 tests, 24 of 24 acceptance tests |
| Time, beta start to report | about 23 minutes | about 16 minutes |
| Approvals by beta | 102, and 4 refusals | 3, and 1 refusal |
| `codex` module times | 11.5 and 12 minutes | 4 and 6 minutes |
| Workers that stalled | 7 | 4, all test writers |

- **The approval load is gone.** `codex` asked for nothing, `agy` for nothing routine. The three
  approvals were all `grok`. The one refusal was `agy`'s chained opening command, which the hook
  sent to beta as intended.
- **Stalled test writers are now what sets the time.** The slowest module went through three test
  writers and took 12 minutes; the others took 3 to 7.
- **Re-use a worker that has just delivered tests.** As replacements, workers that had already
  delivered a test file in the same run delivered again, 3 of 3, in under a minute. One that had
  delivered only code stalled.
- **The three-minute rule costs about four minutes a stall,** and one worker killed at three
  minutes had delivered at 3:38.
- **What beta can no longer see:** with the grant, `codex` runs commands without asking, so beta
  has no list of them. It checked afterwards that only the expected files existed and that the
  earlier builds' folders were untouched.
- **One broken module blocked the other modules' tests** for a few minutes: the stand-ins were
  used only on `ImportError`, and the module had a syntax error. Catch `Exception` there.

**Round 5, the same build again with the new rules,** run on 2026-11-09 from the same spec in a
fresh folder, with the same module split and a new shuffle.

| | Round 4 | Round 5 |
|---|---|---|
| Result | 238 tests and 24 of 24 acceptance tests pass | 239 tests and 24 of 24 acceptance tests pass |
| Time, beta start to report | about 22 minutes | about 23 minutes |
| Workers that stalled | 3 | 7 |
| Time to notice a stall | about 8 minutes, by beta only | 3 to 4 minutes, 5 of 7 by the gamma agent |
| Approvals by beta | 75 | 102, and 4 refusals |
| Files edited by hand by a gamma agent | none | none |

- **Stall detection is fixed.** The timeout wait and the three-minute rule did what they were
  meant to.
- **The build was not faster.** More than twice as many workers stalled, the "wrote tests well"
  list did not predict who would, and the extra checking added about 27 approvals. Quicker
  detection paid for the extra stalls and no more.
- **Approvals are now the limit:** `codex` 58 for two agents, `agy` 40 for one, `grok` 1,
  `claude` 0. The slowest module both times was the `agy` agent's.
- **`agy` ignored its brief's first instruction again** and opened with a chained command that
  searched the home folder. It was refused both times.
- **A worker tried to write a file in the first build's folder.** Its one-file permission block
  stopped it at a prompt, and its gamma agent rejected it.

**Round 4, a real build,** run on 2026-11-09. The task was `tally`, a plain-text expense tracker
in Python: six library modules, a command-line tool and tests, to a written spec. Beta wrote the
shared types and the command-line tool and integrated; each gamma agent owned one module with a
code worker and a test worker.

- **It worked.** Done in about 23 minutes. The team's 238 tests passed, and so did all 24 of
  alpha's acceptance tests, which the team had not seen, on the first run.
- **Six of six code workers were right first time or after one correction.** No gamma agent
  edited a worker's file by hand.
- **Three of six test workers produced nothing** and were replaced from the reserve. See
  [Giving workers real work](#giving-workers-real-work).
- **Nobody noticed the stalled workers until beta read their screens.** See
  [Watching for stalled workers](#watching-for-stalled-workers).
- **72 approvals by beta and one refusal:** `codex` 44, `agy` 27, `grok` 4, `claude` 0.
- **`muse`'s folder-trust prompt appeared and was handled:** its gamma agent, a `codex` agent, saw
  it on the screen and asked beta to approve the key press.
- Alpha saw only beta, and every level cleaned up its own terminals.

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
| `claude` | yes | Fastest, and no prompts, because it runs in auto mode here. That also means its parent never gets to approve or refuse anything it does. |
| `grok` | yes | `--allow 'Bash(hc:*)'` is unreliable: it asked for chained commands and for plain, long `hc run` commands. Two to four approvals a round. It queues incoming messages until its turn ends. |
| `codex` | yes | With the launch grant it asks for nothing and was the second-fastest manager. Without it, its sandbox cannot reach the hc core, so it asks before every `hc` command except `hc --skill`: ten for a quiz, 22 per agent in the build. The most careful reviewer, but it also invents requirements nobody asked for. |
| `agy` | yes | With the launch grant and hook it runs its routine commands unasked. Without them it asks before every command and file read: twelve for a quiz, 27 in the build. Its first move in the build was a chained command that searched the home folder, which was refused. Refusing a command ends its turn, so it then needs an `hc send` to carry on. It can show `done` while a background wait is still running. |
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
- **`claude` agents have no approval layer.** They run in auto mode in this environment, so the
  parent's approval list does not apply to them. Their brief is the only limit; write it
  accordingly, and check afterwards what they touched.
- **Have each level keep a progress log.** Beta appended one timestamped line per event to a file
  (launches, approvals, refusals, reports, reassignments). Alpha could follow the whole tree from
  that file and `hc ls` without talking to anyone but beta.
- **Hold back acceptance tests.** Alpha wrote its own tests from the spec and did not show them to
  the team. That is what made "done" checkable.
- **Budget for approvals.** With default permissions, `codex` and `agy` gamma agents each cost
  their parent ten to twelve approvals in a quiz round and 22 to 40 in a real build. The user can
  remove that cost by granting those harnesses the `hc` commands at launch, as below; an agent
  must not widen permissions on its own.

**Read the hc skill first:** run `hc --skill` and read it before you start anyone. It is the manual
for everything below.

Each subagent is one `hc run` command: a name, a harness, a model, a reasoning level and a prompt. It
starts the harness interactively in its own herdr-core terminal, as a child of yours, so it stays
watchable and steerable. Never use a one-shot mode (`claude -p`, `grok -p`, `agy -p`, `codex exec`,
`muse exec`, `opencode run`).

## Granting gamma agents their hc commands

This is the user's decision, not an agent's. In round 6 it cut beta's approvals from 102 to 3 and
the build from 23 minutes to 16.

- **`codex`:** add `-s workspace-write -a on-request -c 'sandbox_workspace_write.network_access=true'`.
  The sandbox blocks the socket to the hc core unless network access is on. This is wider than
  `hc`: every command it runs can also reach the network, and none of them prompt, so its parent
  sees nothing. Say "no network use" in its brief and check afterwards what it touched.
- **`agy`:** add
  `--mode accept-edits --settings '{"permissions":{"allow":["command(hc)","command(python3 -m unittest)","command(ls)"]}}'`
  and put [`hooks/agy/`](hooks/agy) from this repo into the work folder as `.agents/hooks.json`
  and `.agents/allow-hc.py`. `--settings` lasts for the session and is never saved.
  - The allow-list alone would allow any command starting with `hc`. The hook narrows it: it
    answers `force_ask` unless the command is a single unchained `hc --skill`, `hc ls`, `hc wait`;
    `hc read`, `keys`, `kill` or `rm` on a terminal named `w-GAMMA-N`; `hc send` to `w-GAMMA-N` or
    to the parent; `hc run` of a worker named `w-GAMMA-N` running `opencode` or `muse`;
    `python3 -m unittest`; or `ls` of relative paths.
  - `GAMMA` is the argument in `hooks.json` (`./allow-hc.py argon`). The parent writes its own
    terminal id into `.team/parent-id` before launching.
  - A hook answering `allow` does not skip `agy`'s prompt by itself; only the allow-list does.
    The hook can only make things stricter.
- **`grok`** still asks for a few commands (`stat`, writing its own report) whatever its flags.
- **`claude`** needs nothing: it already runs in auto mode.

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
