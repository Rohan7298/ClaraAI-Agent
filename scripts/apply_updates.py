import sys
import json
from copy import deepcopy

def deep_merge(original, updates):
    """
    Merge updates into original (modifies original in place). Handles nested dicts and lists.
    """
    for key, value in updates.items():
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            deep_merge(original[key], value)
        elif key in original and isinstance(original[key], list) and isinstance(value, list):
            original[key] = list(set(original[key] + value))  # simple merge, avoid duplicates
        else:
            original[key] = value
    return original

def main():
    input_data = sys.stdin.read().strip()
    if not input_data:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)

    try:
        data = json.loads(input_data)
        v1_memo = data.get("v1_memo")
        updates = data.get("updates")
        if not v1_memo or not updates:
            raise ValueError("Missing v1_memo or updates")

        v2_memo = deepcopy(v1_memo)
        v2_memo = deep_merge(v2_memo, updates)
        print(json.dumps(v2_memo, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()