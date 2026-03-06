import sys
import json
from collections.abc import Mapping

def diff_dict(d1, d2, path=""):
    """
    Recursively find differences between two dicts. Returns a list of markdown lines.
    """
    changes = []
    all_keys = set(d1.keys()) | set(d2.keys())
    for key in all_keys:
        new_path = f"{path}.{key}" if path else key
        v1 = d1.get(key) if isinstance(d1, dict) else None
        v2 = d2.get(key) if isinstance(d2, dict) else None

        if isinstance(v1, Mapping) and isinstance(v2, Mapping):
            changes.extend(diff_dict(v1, v2, new_path))
        elif v1 != v2:
            # Convert to string for display
            if isinstance(v1, list) and isinstance(v2, list):
                added = [x for x in v2 if x not in v1]
                removed = [x for x in v1 if x not in v2]
                if added or removed:
                    changes.append(f"- **{new_path}**: changed")
                    if added:
                        changes.append(f"    - Added: {added}")
                    if removed:
                        changes.append(f"    - Removed: {removed}")
            else:
                changes.append(f"- **{new_path}**: changed from `{v1}` to `{v2}`")
    return changes

def main():
    input_data = sys.stdin.read().strip()
    if not input_data:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)

    try:
        data = json.loads(input_data)
        v1 = data.get("v1")
        v2 = data.get("v2")
        account_id = data.get("account_id", "unknown")
        if not v1 or not v2:
            raise ValueError("Missing v1 or v2")

        changes = diff_dict(v1, v2)
        if not changes:
            changelog = f"# Changes for {account_id} (v1 → v2)\n\nNo changes detected."
        else:
            changelog = f"# Changes for {account_id} (v1 → v2)\n\n" + "\n".join(changes)
        print(changelog)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()