import sys
import json
from utils import call_ollama, extract_json_from_llm_output

def main():
    transcript = sys.stdin.read().strip()
    if not transcript:
        print(json.dumps({"error": "No transcript provided"}))
        sys.exit(1)

    prompt = f"""You are an AI assistant that extracts structured information from a demo call transcript.

Extract the following fields from the transcript. If a field is not mentioned, set it to null (or empty list). Add any missing critical information under "questions_or_unknowns". Return ONLY a valid JSON object, no other text.

Fields:
- account_id (string, derive from filename or context if possible)
- company_name (string)
- business_hours (object with days, start, end, timezone, or null)
- office_address (string or null)
- services_supported (list of strings)
- emergency_definition (list of triggers, e.g., ["water leak", "fire"])
- emergency_routing_rules (who to call, order, fallback)
- non_emergency_routing_rules (who to call for non-emergency)
- call_transfer_rules (timeouts, retries, what to say if fails)
- integration_constraints (list of strings, e.g., "never create sprinkler jobs in ServiceTrade")
- after_hours_flow_summary (string)
- office_hours_flow_summary (string)
- questions_or_unknowns (list of strings)
- notes (string)

Transcript:
{transcript}
"""

    llm_output = call_ollama(prompt)
    try:
        memo = extract_json_from_llm_output(llm_output)
        # Ensure all required keys exist
        required_keys = ["account_id", "company_name", "business_hours", "office_address",
                         "services_supported", "emergency_definition", "emergency_routing_rules",
                         "non_emergency_routing_rules", "call_transfer_rules", "integration_constraints",
                         "after_hours_flow_summary", "office_hours_flow_summary",
                         "questions_or_unknowns", "notes"]
        for key in required_keys:
            if key not in memo:
                memo[key] = None if key not in ["services_supported","emergency_definition","integration_constraints","questions_or_unknowns"] else []
        print(json.dumps(memo, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse LLM output: {e}", "raw": llm_output}))
        sys.exit(1)

if __name__ == "__main__":
    main()