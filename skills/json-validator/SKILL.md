---
name: json-validator
version: 1.0.0
description: Validate a JSON string against a minimal schema and pretty-print it.
type: script
runtime: python3
entry: script/run.py
tags: [json, validation, utility]
args:
  type: object
  properties:
    text:
      type: string
      description: The JSON text to validate.
  required: [text]
---
