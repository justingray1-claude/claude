# Justin — Claude Code Context

## About
Justin is the primary user of this Claude Code setup on this machine. Others (Teresa, Ryan, Austin) may use Claude Code from their own subfolders under `~/Documents/claude/`.

## GitHub
- **Account:** justingray1-claude
- **Repo:** https://github.com/justingray1-claude/claude
- **Default branch:** main

## Scheduled Triggers
- **Trigger ID:** trig_01WcbBBowbFtVWEG297DhnEP
- **Name:** Create dummy Python PR
- **Schedule:** Every Monday at 9am PT (cron: `0 17 * * 1` UTC)
- **Task:** Clones repo, creates a branch, adds `utils.py` with dummy Python functions, opens a PR
- **Manage at:** https://claude.ai/code/scheduled/trig_01WcbBBowbFtVWEG297DhnEP

## GitHub Token
- A personal access token with `repo` scope is embedded in the scheduled trigger
- If the token is rotated, update the trigger via Claude Code or at https://claude.ai/code/scheduled

## Preferences
- Prefers Python for code examples
- Casual setup — shares this Mac with others but uses separate Anthropic accounts and working directories for isolation

## Working Directory
- Justin's working directory: `~/Documents/claude/Justin/`
