import sys
import json
from utils import call_ollama, extract_json_from_llm_output

def main():
    transcript = sys.stdin.read().strip()
    if not transcript:
        print(json.dumps({"error": "No transcript provided"}))
        sys.exit(1)

    prompt = f"""You are an AI assistant that extracts updates from an onboarding call transcript.

Extract any changes or additions to the following fields. If a field is not mentioned, omit it. Return ONLY a JSON object containing only the fields that have changed or been added. Do not include fields that remain the same.

Possible fields (same as in demo memo):
- company_name
- business_hours (object with days, start, end, timezone)
- office_address
- services_supported (list)
- emergency_definition (list)
- emergency_routing_rules
- non_emergency_routing_rules
- call_transfer_rules
- integration_constraints (list)
- after_hours_flow_summary
- office_hours_flow_summary
- notes

Transcript:
{transcript}
"""

    llm_output = call_ollama(prompt)
    try:
        updates = extract_json_from_llm_output(llm_output)
        print(json.dumps(updates, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse LLM output: {e}", "raw": llm_output}))
        sys.exit(1)

if __name__ == "__main__":
    main()