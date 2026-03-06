# Clara AI Pipeline

Automates transcript-to-agent configuration for multiple service accounts using a local LLM (Ollama).

The project runs two stages:
1. Demo stage (`v1`): extract a structured memo from demo-call transcripts and generate an initial agent spec.
2. Onboarding stage (`v2`): extract onboarding updates, merge into `v1`, regenerate the agent spec, and produce a changelog.

## What This Repository Does

Given transcript files in:
- `data/transcripts_demo/*.txt`
- `data/transcripts_onboarding/*.txt`

It generates per-account artifacts in:
- `outputs/accounts/<account_id>/v1/memo.json`
- `outputs/accounts/<account_id>/v1/agent_spec.json`
- `outputs/accounts/<account_id>/v2/memo.json`
- `outputs/accounts/<account_id>/v2/agent_spec.json`
- `outputs/accounts/<account_id>/v2/changelog.md`

It also appends execution logs to:
- `outputs/tasks.json`

## Project Structure

```text
requirements.txt
run_pipeline.py
scripts/
  utils.py
  extract_demo.py
  extract_onboarding.py
  apply_updates.py
  diff_memo.py
  generate_agent_spec.py
workflows/
  pipeline_a_demo.json
  pipeline_b_onboarding.json
data/
  transcripts_demo/
  transcripts_onboarding/
outputs/
```

## Prerequisites

- Python 3.9+ (3.10+ recommended)
- Ollama installed and running locally
- Ollama model: `llama3.2:3b`

Install the model if needed:

```powershell
ollama pull llama3.2:3b
```

Start Ollama (if not already running):

```powershell
ollama serve
```

## Setup

1. Create and activate a virtual environment (recommended).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. (Optional) Copy env template for local overrides.

```powershell
copy .env.example .env
```

Notes:
- The Python scripts only require `requests` from `requirements.txt`.
- `OLLAMA_URL` defaults to `http://localhost:11434` in code (`scripts/utils.py`).
- `.env.example` includes values useful for container/n8n usage.

## Quick Start

Run the full pipeline:

```powershell
python run_pipeline.py
```

What happens:
1. Checks Ollama availability and verifies `llama3.2:3b` exists.
2. Processes each file in `data/transcripts_demo` into `v1` outputs.
3. Processes each file in `data/transcripts_onboarding` into `v2` outputs (requires corresponding `v1` memo).
4. Writes/updates `outputs/tasks.json` with timestamped task entries.

## Input Naming Convention

Use matching filenames across both transcript folders. The filename stem becomes `account_id`.

Example:
- `data/transcripts_demo/acme_plumbing.txt`
- `data/transcripts_onboarding/acme_plumbing.txt`

Produces:
- `outputs/accounts/acme_plumbing/v1/...`
- `outputs/accounts/acme_plumbing/v2/...`

## Script Overview

- `scripts/extract_demo.py`
  - Reads demo transcript from `stdin`
  - Calls Ollama
  - Emits normalized memo JSON

- `scripts/extract_onboarding.py`
  - Reads onboarding transcript from `stdin`
  - Calls Ollama
  - Emits only changed fields as JSON

- `scripts/apply_updates.py`
  - Deep-merges onboarding updates into `v1` memo
  - Merges lists by union

- `scripts/generate_agent_spec.py`
  - Converts memo JSON into `agent_spec.json`
  - Builds system prompt and call-handling behavior

- `scripts/diff_memo.py`
  - Generates markdown changelog between `v1` and `v2`

- `run_pipeline.py`
  - Orchestrates end-to-end processing for all accounts

## Running Individual Scripts

### Extract Demo Memo

```powershell
Get-Content data/transcripts_demo/acme_plumbing.txt -Raw | python scripts/extract_demo.py
```

### Extract Onboarding Updates

```powershell
Get-Content data/transcripts_onboarding/acme_plumbing.txt -Raw | python scripts/extract_onboarding.py
```

### Apply Updates

```powershell
$payload = @'
{"v1_memo": {"company_name": "Acme"}, "updates": {"notes": "New routing"}}
'@
$payload | python scripts/apply_updates.py
```

### Generate Agent Spec

```powershell
Get-Content outputs/accounts/acme_plumbing/v1/memo.json -Raw | python scripts/generate_agent_spec.py
```

### Generate Changelog

```powershell
$payload = @'
{"v1": {"company_name": "Acme"}, "v2": {"company_name": "Acme", "notes": "Updated"}, "account_id": "acme_plumbing"}
'@
$payload | python scripts/diff_memo.py
```

## n8n Workflows

`workflows/` contains exported JSON workflow templates:
- `pipeline_a_demo.json`
- `pipeline_b_onboarding.json`

These mirror the same Python scripts and output contracts used by `run_pipeline.py`.

## Troubleshooting

- `Ollama is not running`
  - Start Ollama: `ollama serve`

- `llama3.2:3b not found`
  - Pull model: `ollama pull llama3.2:3b`

- `No v1 memo found for <account_id>` during onboarding
  - Ensure the matching demo transcript was processed first

- `Failed to parse LLM output`
  - Re-run the command (scripts include retries)
  - Check transcript quality and model availability

## Notes for Production Hardening

Current implementation is suitable for local/demo workflows. For production use, consider:
- schema validation for all JSON outputs
- deterministic list merge order (current merge uses set semantics)
- stronger error handling and retry policies
- audit logging and idempotency safeguards
- unit tests for merge/diff/spec generation logic
