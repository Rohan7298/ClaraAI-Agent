import sys
import json

def main():
    memo_json = sys.stdin.read().strip()
    if not memo_json:
        print(json.dumps({"error": "No memo provided"}))
        sys.exit(1)

    try:
        memo = json.loads(memo_json)
    except Exception as e:
        print(json.dumps({"error": f"Invalid memo JSON: {e}"}))
        sys.exit(1)

    # Helper to get nested values safely
    def get_nested(d, keys, default=""):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, {})
            else:
                return default
        return d if d is not None else default

    company = memo.get("company_name", "Unknown Company")
    business_hours = memo.get("business_hours", "Not specified")
    if isinstance(business_hours, dict):
        business_hours = f"{business_hours.get('days','')} {business_hours.get('start','')}-{business_hours.get('end','')} {business_hours.get('timezone','')}".strip()

    emergency_routing = memo.get("emergency_routing_rules", "Default emergency routing")
    call_transfer = memo.get("call_transfer_rules", "Default transfer rules")
    after_hours = memo.get("after_hours_flow_summary", "Default after hours handling")
    office_hours = memo.get("office_hours_flow_summary", "Default office hours handling")
    address = memo.get("office_address", "")

    # Build system prompt following conversation hygiene
    system_prompt = f"""You are the virtual assistant for {company}.

Office hours: {business_hours}
Office hours flow: {office_hours}
After hours flow: {after_hours}
Emergency routing: {emergency_routing}
Call transfer protocol: {call_transfer}

Guidelines:
- Greet the caller politely and ask for their name and the purpose of the call.
- Do not ask more questions than necessary; collect only what is needed for routing or dispatch.
- If it's an emergency, collect name, number, and address immediately, then attempt transfer.
- If transfer fails, take a message and assure the caller of a quick callback.
- Never mention "function calls", "tools", or technical details to the caller.
- Keep the conversation natural and professional.
- Confirm next steps before ending the call.
- Always ask "Is there anything else I can help you with?" before closing."""

    spec = {
        "agent_name": f"{company} AI Agent",
        "voice_style": "friendly professional",
        "system_prompt": system_prompt,
        "variables": {
            "timezone": get_nested(memo, ["business_hours", "timezone"], "America/New_York"),
            "address": address
        },
        "tool_invocation_placeholders": [],
        "call_transfer_protocol": call_transfer,
        "fallback_protocol": "If transfer fails, take a message and assure quick callback.",
        "version": memo.get("_version", "v1")   # will be set externally
    }

    print(json.dumps(spec, indent=2))

if __name__ == "__main__":
    main()