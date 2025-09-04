#!/bin/bash
# --------------------------------------------------------------------
# PostToolUse hook for Claude Code
#
# This script runs automatically *after* Claude executes certain tools
# (in this case: Edit, Write, MultiEdit).
#
# Purpose:
#   - Maintain an audit trail of when Claude edits/writes files.
#   - Store logs in `.claude/logs/tool-usage.log` with timestamps.
#
# NOTE:
#   - Claude expects hooks to output JSON.
#   - Returning `{}` at the end ensures success and avoids blocking.
# --------------------------------------------------------------------

# 1. Capture the current timestamp in a readable format
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# 2. Ensure the logs directory exists (safe even if it already exists)
mkdir -p .claude/logs

# 3. Append a log entry to the log file
#    Each line records when Claude made an edit/write.
echo "[$timestamp] Claude made an edit" >> .claude/logs/tool-usage.log

# 4. Output minimal valid JSON so Claude knows the hook succeeded
#    (required by Claude Code’s hook system)
echo "{}"
