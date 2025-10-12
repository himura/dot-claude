#!/usr/bin/env python3
import json
import sys
import re

# Read hook input from stdin
hook_input = json.load(sys.stdin)

# Extract the Bash command
command = hook_input.get("tool_input", {}).get("command", "")

# Check if the command contains 'stack build'
if re.search(r'\bstack\s+build\b', command):
    print("❌ Use 'stack test --fast' instead of 'stack build'", file=sys.stderr)
    print("", file=sys.stderr)
    print("Reason: 'stack build' causes unnecessary rebuilds.", file=sys.stderr)
    print("Refer to CLAUDE.md for the correct build & test workflow.", file=sys.stderr)
    # Exit code 2 blocks the tool call
    sys.exit(2)

# Allow the command to proceed
sys.exit(0)
