#!/usr/bin/env python3
"""json-validator skill: validates JSON passed via SKILL_INPUT env var."""
import json
import os
import sys

raw = os.environ.get("SKILL_INPUT", "{}")
try:
    payload = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"ERROR: cannot parse SKILL_INPUT as JSON: {e}", file=sys.stderr)
    sys.exit(2)

text = (payload.get("text") or "").strip()
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    print(f"INVALID JSON: {e}", file=sys.stderr)
    sys.exit(1)

print(json.dumps(data, indent=2, ensure_ascii=False))
print(f"\nvalid: true, keys: {len(data) if isinstance(data, dict) else 'n/a'}", file=sys.stderr)
