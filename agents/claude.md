# Starting a Claude subagent

Every way to start a Claude subagent under Herdr, and every option. For the team, the briefs and the
wait and cleanup rules, see [AGENTS.md](../AGENTS.md).

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

## Ways to start

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

## `hc run` options

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

## `claude` options

These come from `claude --help` for the version under [Tested with](../AGENTS.md#tested-with). The session is
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

## What Claude may ask

- **A folder it hasn't seen:** a trust dialog appears with **"No, exit" selected**, so a plain `enter`
  would quit. Use `hc keys <t> down enter`, and only for the folder you were asked to work in.
  - hc doesn't report this dialog as `blocked`, and it doesn't wake `hc wait`. When starting in a new
    folder, run `hc read <t> --lines 0` right after launch.
  - The task survives: in testing, it ran after the dialog was accepted.
- **Permission prompts:** these do show as `blocked`. A file-write dialog offers "1. Yes", then "2. Yes,
  and switch to accept edits", then "3. No". `hc keys <t> enter` allows once, and `hc keys <t> esc`
  cancels. Don't pick option 2.
- **In auto mode,** it asked for nothing in the project folder, not even for `hc send`.
