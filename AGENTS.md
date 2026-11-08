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
- Check that the task arrived. Template launches report `first_message.sent`; if it's `false`, the
  task never arrived. Direct launches don't report it, so read the screen if a child sits idle. Clear
  any startup or trust prompt and check again before sending the task yourself. Never resend blindly.
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
- **Claude:** `claude --model <model> --effort high "<task>"`. Every other way to start it, and every
  option, is in [Starting a Claude subagent](#starting-a-claude-subagent).
- **Muse Code:** `muse --model muse-spark-1.3-contributor --reasoning-effort high "<task>"`
  - Muse's sandbox blocks `hc send` with a read-only-filesystem error and offers no approval for it,
    even with `--approval-judge off`. So its brief says: don't run `hc send`; just write the output
    file and end the turn.
  - Muse reports its own `done` status, which `hc wait --children any` picks up.
  - Don't disable its sandbox.

## Starting a Claude subagent

The usual command has three parts: `hc run` options that set up the terminal, `claude` options that
set up the agent, and the task.

```sh
hc run --bg --name beta-sonnet --cwd "$PWD" -- claude --model claude-sonnet-5-5 --effort high "<task>"
```

Then wait, read the result, and clean up:

```sh
hc wait --children any --timeout 170   # returns on a report, a block, an exit or a timeout
hc read beta-sonnet --lines 0          # see its screen
hc kill beta-sonnet                    # once you've checked the result
hc rm beta-sonnet
```

The `--` is optional here; it just marks where `hc run`'s options end. Run this from inside a
Herdr/hc terminal, or the child gets no parent and `$HC_TERMINAL_ID` may be unset. A task in double
quotes can use `$HC_TERMINAL_ID`, because your shell fills it in with your ID before launch. A brief
file can't: it's plain text, so the child's shell would fill in the child's own ID.

### Ways to start

| Way | Command | Use it when |
|---|---|---|
| With a task (default) | `hc run --bg --name <name> -- claude "<task>"` | A subagent has one job to do. |
| Empty, then send | `hc run --bg --name <name> -- claude`, then `hc wait <name>`, then `hc send <name> "<task>"` | You don't know the task yet. Wait first: a message sent while it boots can be dropped. |
| From a template | `hc run <template> "<task>"` | A ready-made role fits. `hc templates` lists them; the files are in `~/.config/herdr-core/templates/`. |
| In its own Herdr tab | `herdr-app do tab.new --name "<name>" --argv '["claude"]' --task "<task>"` | The user wants it as a normal tab, not a sub-agent. |
| Beside a pane | `herdr-app do pane.split --direction right --argv '["claude"]'` | The user wants to see it next to their work. It starts without a task. |
| In a chosen Herdr tab | `hc run --keep --label herdr.space=<id> --label herdr.tab=<id> -- claude` | It should appear in a specific space and tab. |

The first two were run in testing. The others come from the Herdr and hc manuals and weren't run. The
only template here is `researcher`, a lead that starts three Codex subagents of its own.

A sub-agent has no pane of its own. It's listed in Herdr's Agents list; `terminal.peek` opens it and
`terminal.keep` gives it a pane.

Don't start Claude these ways: `claude -p` is one-shot, `claude --bg` hands the session to Claude's own
background manager (`claude agents`) instead of hc, and a plain shell `&` job is invisible to Herdr.

### `hc run` options

| Option | What it does |
|---|---|
| `--bg` | Returns at once instead of streaming the agent's screen into your output. Always use it for agents. |
| `--name <name>` | Names the terminal: unique among live terminals, 1-32 of `a-z 0-9 - _`. |
| `--cwd <dir>` | Working directory. Default: where `hc` runs. With `--on`: that machine's home. |
| `--on <machine>` | Runs it on another machine (`hc machine ls`). Its address becomes `machine/t7`. |
| `--label <k=v>` | Adds labels (repeatable). `herdr.space` and `herdr.tab` place it in Herdr. |
| `--parent <t>` | Sets the parent terminal. Default: the terminal it's started from. |
| `--no-parent` | Gives it no parent, even when started from a terminal. |
| `--outlive-parent` | Keeps it running when its parent's program ends. By default it ends too. |
| `--no-notify` | Stops notes about it being typed into its parent. |
| `--rm` | Removes it right after it exits. Skip this if you still want to `hc read` it. |
| `--keep` | Replaces a lost program with a shell in the same place. It never re-runs the original command. |
| `--timeout <s>` | Seconds before a wait checks in, leaving it running. Default: config `wait_timeout`, else 180. |
| `--json` | JSON output even in a terminal. Piped `--bg` output is already JSON; in a terminal it prints `t37 started`. |

### `claude` options

These come from `claude --help` for the version under [Tested with](#tested-with). The session is
interactive unless you pass `-p`.

**Watch out: some options take several values and swallow the task.** `--allowedTools`,
`--disallowedTools`, `--tools`, `--add-dir`, `--mcp-config`, `--file` and `--betas` all accept a list.
In testing, `claude --allowedTools 'Bash(hc send:*)' "<task>"` treated the task as another tool name:
Claude opened idle at an empty prompt and nothing reported a failure. Put the task first:

```sh
hc run --bg --name <name> -- claude "<task>" --model <model> --effort high --permission-mode manual --allowedTools 'Bash(hc send:*)'
```

**Model and effort**

| Option | What it does |
|---|---|
| `--model <model>` | An alias (`fable`, `opus`, `sonnet`) or a full name such as `claude-sonnet-5-5`. |
| `--effort <level>` | `low`, `medium`, `high`, `xhigh` or `max`. The team uses `high`. |
| `--fallback-model <models>` | Comma-separated models to try when the main one is overloaded or unavailable. |

**Permissions**

| Option | What it does |
|---|---|
| `--permission-mode manual` | Asks before actions that need approval. In testing, a write stopped at a prompt and hc showed `blocked`. |
| `--permission-mode acceptEdits` | Approves file edits without asking. |
| `--permission-mode auto` | Claude decides what's safe to run without asking. The user's setup already runs this way. |
| `--permission-mode dontAsk` | Doesn't prompt: anything not already allowed is refused. |
| `--permission-mode plan` | Plans without making changes. |
| `--permission-mode bypassPermissions` | Skips all checks. Don't use it for reviewers. |
| `--allowedTools <tools>` | Tools allowed without asking, e.g. `'Bash(hc send:*)' Edit`. In testing, that rule let `hc send` run under `manual`. |
| `--disallowedTools <tools>` | Tools to deny, in the same format. |
| `--tools <tools>` | Limits the available built-in tools: names such as `Bash,Edit,Read`, `default`, or `""` for none. |
| `--add-dir <dirs>` | Extra directories its tools may access. |
| `--restricted` | Removes command-running tools and WebFetch unless `--tools` names them, ignores user, project and local settings, confines file tools to the working directories, and refuses `bypassPermissions`. |
| `--dangerously-skip-permissions` | Bypasses all checks. Recommended only for sandboxes with no internet access. Don't use it for reviewers. |
| `--allow-dangerously-skip-permissions` | Makes bypassing available without turning it on. The same warning applies. |

**Instructions and context**

| Option | What it does |
|---|---|
| `--system-prompt <prompt>` | Replaces the system prompt. |
| `--append-system-prompt <prompt>` | Adds to the default system prompt. |
| `--system-prompt-snapshot <on\|off>` | `on` records the prompt once per conversation and reuses it. `off` renders it fresh on every request. |
| `--exclude-dynamic-system-prompt-sections` | Moves per-machine details from the system prompt into the first user message, for better prompt-cache reuse. |
| `--agent <agent>` | Which agent runs this session. |
| `--agents <json>` | Defines custom agents as JSON. |
| `--brief` | Enables the SendUserMessage tool. |
| `--autocompact <auto\|tokens>` | Auto-compact window size: `auto`, or 100k to 1M tokens. |
| `--prompt-suggestions [value]` | Turns prompt suggestions on or off. |
| `--file <specs>` | Downloads file resources at startup, as `file_id:relative_path`. |

**Sessions**

| Option | What it does |
|---|---|
| `-n, --name <name>` | Display name in the prompt box, `/resume` picker and terminal title. It's separate from `hc run --name`. |
| `-c, --continue` | Continues the most recent conversation in the current directory. |
| `-r, --resume [value]` | Resumes by session ID or name, or opens a picker. |
| `--fork-session` | With `--resume` or `--continue`, uses a new session ID instead of reusing the original. |
| `--session-id <uuid>` | Uses a specific session ID. |
| `--from-pr [value]` | Resumes a session linked to a PR, or opens a picker. |

**Isolation and configuration**

| Option | What it does |
|---|---|
| `-w, --worktree [name]` | Creates a new git worktree for this session. |
| `--tmux` | Creates a tmux session for the worktree. Requires `--worktree`. |
| `--settings <file-or-json>` | Loads additional settings. |
| `--setting-sources <sources>` | Which settings to load: `user`, `project`, `local`. |
| `--safe-mode` | Disables customizations (CLAUDE.md, skills, plugins, hooks, MCP servers and more), for troubleshooting. |
| `--bare` | Minimal mode: skips hooks, LSP, plugin sync, auto-memory and CLAUDE.md discovery. Auth must be an API key, so it won't use a subscription login. |
| `--mcp-config <configs>` | Loads MCP servers from JSON files or strings. |
| `--strict-mcp-config` | Uses only the servers from `--mcp-config`. |
| `--plugin-dir <path>` | Loads a plugin from a directory or `.zip` for this session (repeatable). |
| `--plugin-url <url>` | Fetches a plugin `.zip` for this session (repeatable). |
| `--disable-slash-commands` | Disables all skills and commands. |
| `--chrome`, `--no-chrome` | Turns Claude in Chrome on or off. |
| `--ide` | Connects to an IDE on startup if exactly one valid IDE is available. |
| `--betas <betas>` | Beta headers for API requests (API key users only). |
| `--ax-screen-reader` | Screen-reader friendly output. |

**Debugging and other commands**

| Option | What it does |
|---|---|
| `-d, --debug [filter]` | Debug mode, with optional category filtering. |
| `--debug-file <path>` | Writes debug logs to a file, which also turns debug mode on. |
| `--verbose` | Overrides the verbose mode setting. |
| `-v, --version`, `-h, --help` | Prints the version or the help. |

**Not for subagents under hc**

These leave the terminal, run one-shot, or apply only to one-shot runs.

| Options | Why |
|---|---|
| `-p, --print` | One-shot, so it can't be watched or steered. It also skips the workspace trust dialog. |
| `--output-format`, `--input-format`, `--json-schema`, `--max-budget-usd`, `--no-session-persistence`, `--permission-prompts`, `--forward-subagent-text`, `--include-partial-messages`, `--include-hook-events`, `--replay-user-messages` | Output and limits for `-p` runs; most work only with `--print`. |
| `--bg, --background` | Runs under Claude's own background manager, not hc. |
| `--cloud`, `--environment`, `--teleport`, `--remote-control`, `--remote-control-session-name-prefix` | Cloud and remote sessions. |
| `--desktop` | Opens the Claude Desktop app instead of the terminal. |

### What Claude may ask

- **A folder it hasn't seen:** a trust dialog appears with **"No, exit" selected**, so a plain `enter`
  would quit. Use `hc keys <t> down enter`, and only for the folder you were asked to work in.
  - hc doesn't report this dialog as `blocked`, and it doesn't wake `hc wait`. When starting in a new
    folder, run `hc read <t> --lines 0` right after launch.
  - The task survives: in testing, it ran after the dialog was accepted.
- **Permission prompts:** these do show as `blocked`. A file-write dialog offers "1. Yes", then "2. Yes,
  and switch to accept edits", then "3. No". `hc keys <t> enter` allows once, and `hc keys <t> esc`
  cancels. Don't pick option 2.
- **In auto mode,** it asked for nothing in the project folder, not even for `hc send`.

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
- **Claude asks only if its permission mode says so.** With the user's auto mode, it asked for
  nothing in the project folder. In a folder it hasn't seen, or under `--permission-mode manual`, it
  does ask. See [What Claude may ask](#what-claude-may-ask).
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
