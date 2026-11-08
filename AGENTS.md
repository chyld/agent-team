# Running team beta in Herdr

How **alpha** starts, watches and cleans up the **beta** reviewers when it runs inside a Herdr
terminal. The team and the workflow are in [README.md](README.md). Everything here was tested on
2026-11-07 by running all eleven reviewers twice. Two beta review rounds checked it against each
CLI's `--help` output and what the reviewers actually did. The CLI versions tested are listed at the
end, and the details can change between versions.

You are running inside a Herdr terminal (`$HC_TERMINAL_ID`, e.g. `t1d`). Start every subagent as a
herdr-core terminal with `hc` so it becomes your child and the user can watch it in Herdr's Agents
list. Never start agents as plain background shell jobs; Herdr can't see those. Read `hc --skill`
once for the full manual.

## Launch

- Always use `hc run --bg --name <name> -- <cli> ... "<task>"`. Names must be unique and use only
  1-32 characters from `a-z 0-9 - _`, so don't paste a model ID in: no dots or slashes. Use the
  names in the [team table](#team). Put the task in the launch command, because a message sent
  while it boots can be dropped.
- If a launch result shows `first_message.sent: false`, the task never arrived. Read the screen,
  clear any startup or trust prompt, and check again before sending the task yourself. Never resend
  blindly.
- Run agents interactively, never in one-shot mode (`claude -p`, `grok -p`, `agy -p`, `codex exec`,
  `muse exec`, `opencode run`), so they stay watchable and steerable. Codex's own `-p` is
  `--profile`, not print mode.
- Put long instructions in a brief file, and make the task one line: "Read <brief> and follow it
  exactly. Your name is <name>. Your output file is <path>."

## The brief

Every brief says:

- **Scope:** what to review, and which reads and commands are in scope. For example: read-only
  `--help`/`help` commands, `hc --skill`, and reads of files under `<input folder>`. With that
  written down you can approve those requests quickly and spot anything outside them.
- **Writes:** only their own output file.
- **Limits:** no subagents, and never kill any process.
- **Reporting:** when finished, `hc send <alpha-id> "done: <path>"`; if stuck,
  `hc send <alpha-id> "stuck: <reason>"`.
  - Write alpha's terminal ID in as a literal (e.g. `hc send t1d ...`). Never write
    `$HC_TERMINAL_ID` there: in the child it expands to the child's own ID, and the report goes to
    itself.
  - Tell them to run `hc send` as a command on its own, not chained with `&&` or `;`. Otherwise
    Grok's and OpenCode's `hc send` allow rules don't match, and they ask instead.
  - For Muse, replace the report line with "don't run `hc send`; write your output file and end your
    turn" (see [Muse](#per-cli-launch-commands-all-at-high-reasoning)).

## Per-CLI launch commands (all at high reasoning)

- **Codex:** `codex --no-daemon -m <model> -c model_reasoning_effort=high -s workspace-write -a on-request "<task>"`
  `--no-daemon` is required under hc. Both GPT-6.1 models default to low effort, so always set
  high.
- **Grok:** `grok -m grok-4.7 --reasoning-effort high --permission-mode acceptEdits --allow 'Bash(hc send:*)' "<task>"`
- **Antigravity:** `agy --model gemini-4-argon-high --effort high --mode accept-edits -i "<task>"`
- **OpenCode Go:** its TUI has no `-m`, so the model goes in `OPENCODE_CONFIG_CONTENT`. `<model>` is
  the bare name, e.g. `hy4`, not `opencode-go/hy4`.

  ```sh
  env 'OPENCODE_CONFIG_CONTENT={"model":"opencode-go/<model>#high","permission":{"edit":{"*":"ask","<abs-output-path>":"allow","<rel-output-path>":"allow"},"bash":{"*":"ask","hc send *":"allow"},"webfetch":"deny"}}' opencode --standalone --prompt "<task>"
  ```

  - **Always pass a permission block.** Without one, OpenCode asks for nothing. In one test a
    reviewer wrote about 60 MB to `/tmp` and fetched a web page, both outside its brief.
  - **What the block does:** the edit tool may write only the output file. List that file both as an
    absolute path and relative to the launch folder; the test didn't show which form matched.
    Shell commands that start with `hc send` are allowed, every other shell command or edit asks,
    and the web-fetch tool is denied.
  - **It is not a sandbox.** These are tool rules: a shell command you approve can still write
    anywhere, so read each one before allowing it.
  - **`--standalone`** gives each reviewer its own private server instead of the shared background
    service.
- **Claude:** `claude --model <model> --effort high "<task>"`
- **Muse Code:** `muse --model muse-spark-1.3-contributor --reasoning-effort high "<task>"`
  - Muse's sandbox blocks `hc send` with a read-only-filesystem error and offers no approval for it,
    even with `--approval-judge off`. So its brief says: don't run `hc send`; just write the output
    file and end the turn.
  - Muse reports its own `done` status, which `hc wait --children any` picks up.
  - Don't disable its sandbox.

## Expect these prompts

- **Folder trust on first run:** Grok wants `hc keys <t> y`. Antigravity and Muse want
  `hc keys <t> enter`. Accept only for the project folder you were asked to work in. Muse's trust
  prompt is not flagged as `blocked` and doesn't wake `hc wait`, so right after launching Muse, run
  `hc read <t> --lines 0` and accept the prompt before your first wait.
- **Antigravity asks before every file read and every shell command, including `hc send`.**
  - Its dialogs have "1. Yes, allow access" / "1. Yes, run command" selected, so
    `hc keys <t> enter` allows once. Never pick the "always allow" options.
  - `accept-edits` auto-approved its output-file write.
  - Approve reads of the brief and input files, in-scope commands from the brief, and the exact
    `hc send` to you.
  - A review can take 30+ approvals, so check it on every `blocked` notice.
- **Grok asks before every Bash command except `hc send`, and asked before writing its output file
  despite `acceptEdits`.**
  - Its dialog has "Yes, proceed" selected (option 2 or 3, after the always-approve options), so
    `hc keys <t> enter` allows once.
  - Pressing the "No, reject" option's number rejects.
  - Never always-approve.
- **Codex's sandbox blocks `hc send`:** the dialog shows "1. Yes, proceed (y)"; approve that exact
  command with `hc keys <t> y`.
- **OpenCode asks before shell commands other than a bare `hc send`, and before edits to any file
  other than its output file.**
  - The prompt shows `Allow once  Always allow  Reject`, with Allow once selected:
    `hc keys <t> enter` allows once, and `hc keys <t> right right enter` rejects.
  - A reject ends OpenCode's whole turn, so `hc send` a follow-up saying what to do next. One child
    followed such a message. Another called it "a relayed message" but still carried on. Read its
    screen to check.
  - Never pick "Always allow".
- **Claude:** no prompts were seen in testing. Whether it asks depends on the user's Claude
  settings, so treat any prompt it shows like the others.
- **Anything else:** if a blocked agent wants something outside its brief (another file, network,
  installs, destructive commands), read the screen and ask the user. Never `--force` past a
  permission. Antigravity's `accept-edits` and Codex's `workspace-write` don't limit writes to the
  output file, so for them the brief is the main limit.

## Watch

- Wait with `hc wait --children any --timeout 170` in a loop, and handle each event (blocked,
  done, message, exit) before waiting again. `--children all` also returns while some children are
  blocked, so use it only to wait for everyone to stop, then check each one's status. Never sleep or
  poll.
- `reason: message` means a child report arrives as your next input. Note it and wait again.
- On a `blocked` notice, run `hc read <t> --lines 0` and deal with it at once. Don't let blocked
  children queue up while you read other results.
- `hc ls` lists live terminals with their status (piped output is JSON). "done" from an agent (a
  report, or a `done` status for Muse) means check that its output file exists, then read it. Never
  assume success.
- If a child keeps probing past its scope, steer it with `hc send <t> "<finish now>"` while it's
  working. `send` refuses while it's blocked, so deal with the prompt first. If the message then sits
  queued, as Antigravity's did, run `hc interrupt <t>`, read the screen, and press
  `hc keys <t> enter` to submit it.
- While they work, do useful work yourself, such as reading results that have already arrived.

## Stop and clean up

- Stop one: `hc kill <name>`, then `hc rm <name>`. `rm` only removes a finished terminal, so
  check `hc ls --all` afterwards (plain `hc ls` hides finished ones) and retry `rm` if it's still
  listed. Stop all: loop over the names you started.
- Only touch terminals you started. Never `pkill` by name, and never `hc server stop`.
- If the user says stop, stop everything immediately, then report which outputs finished and which
  didn't.
- When you're done, kill and remove every helper.

## Team

Keep this table in step with the one in [README.md](README.md).

| CLI | Model | Name |
|---|---|---|
| Claude | `claude-sonnet-5-5` | `beta-sonnet` |
| Codex | `gpt-6.1-sol` | `beta-sol` |
| Codex | `gpt-6.1-terra` | `beta-terra` |
| Grok | `grok-4.7` | `beta-grok` |
| Muse Code | `muse-spark-1.3-contributor` | `beta-muse` |
| OpenCode Go | `deepseek-v4.1-flash` | `beta-deepseek` |
| OpenCode Go | `minimax-m3.1-flash` | `beta-minimax` |
| OpenCode Go | `glm-5.3-flash` | `beta-glm` |
| OpenCode Go | `kimi-k3.1-pro` | `beta-kimi` |
| OpenCode Go | `hy4` | `beta-hy4` |
| Antigravity | `gemini-4-argon-high` | `beta-argon` |

## Tested with

| CLI | Version |
|---|---|
| Claude Code | 2.1.319 |
| Codex | codex-cli 0.167.0 |
| Grok | 1.0.77 |
| Antigravity (`agy`) | 1.5.3 |
| OpenCode | 2.2.6 |
| Muse Code | 1.4.14 |
