# Starting a Claude subagent

Run these from inside a Herdr terminal:

```sh
hc run --bg --name demo -- claude --model claude-sonnet-5-5 --effort high "<task>"
hc wait --children any --timeout 170
hc read demo --lines 0
hc kill demo
hc rm demo
```

These start it, wait for news from it, show its screen, then stop and remove it.

To get a report back, end the task with: `Then run: hc send $HC_TERMINAL_ID "done"`. In double quotes,
your shell fills in your own ID. In a brief file it wouldn't, so write your real ID there.

## Options

| Option | What it does |
|---|---|
| `--bg` | Returns right away instead of streaming the agent's screen |
| `--name` | Names it: 1-32 of `a-z 0-9 - _` |
| `--cwd` | Sets the folder it runs in |
| `--model` | Picks the model |
| `--effort` | Sets the reasoning effort: `low` to `max` |
| `--permission-mode` | Sets what it may do without asking, e.g. `manual` |

`hc run --help` and `claude --help` list the rest.

## Watch out

- **Task disappears:** with `--allowedTools`, put the task first, or Claude takes it as a tool name and
  sits idle: `claude "<task>" --allowedTools 'Bash(hc send:*)'`.
- **New folder:** Claude asks whether to trust it, and hc doesn't flag that. Check with `hc read` right
  after launch, then accept with `hc keys <name> down enter`.
- **Blocked:** run `hc read <name> --lines 0` to see what it wants. `hc keys <name> enter` allows the
  selected option once, and `hc keys <name> esc` cancels.
