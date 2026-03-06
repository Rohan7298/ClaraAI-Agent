import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
DEMO_FOLDER = "data/transcripts_demo"
ONBOARDING_FOLDER = "data/transcripts_onboarding"
OUTPUT_BASE = "outputs/accounts"

def ensure_folders():
    """Create necessary folders if they don't exist"""
    folders = [DEMO_FOLDER, ONBOARDING_FOLDER, OUTPUT_BASE]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    print("✅ Folders ready")

def read_file_content(file_path):
    """Read a file with proper encoding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def process_demo_file(transcript_path, account_id):
    """Process a single demo file"""
    print(f"\n📄 Processing demo: {account_id}")
    
    # Read transcript
    transcript = read_file_content(transcript_path)
    
    # Run extraction
    result = subprocess.run(
        ['python', 'scripts/extract_demo.py'],
        input=transcript,
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    if result.returncode != 0:
        print(f"❌ Error extracting demo: {result.stderr}")
        return False
    
    # Parse memo
    try:
        memo = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON output: {result.stdout[:200]}")
        return False
    
    memo['account_id'] = account_id
    
    # Generate agent spec
    spec_result = subprocess.run(
        ['python', 'scripts/generate_agent_spec.py'],
        input=json.dumps(memo),
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    if spec_result.returncode != 0:
        print(f"❌ Error generating spec: {spec_result.stderr}")
        return False
    
    try:
        spec = json.loads(spec_result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Invalid spec JSON: {spec_result.stdout[:200]}")
        return False
    
    spec['version'] = 'v1'
    
    # Save outputs
    output_dir = Path(OUTPUT_BASE) / account_id / 'v1'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'memo.json', 'w', encoding='utf-8') as f:
        json.dump(memo, f, indent=2)
    
    with open(output_dir / 'agent_spec.json', 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2)
    
    # Log task
    log_task(account_id, 'v1', 'processed')
    
    print(f"✅ Completed demo: {account_id}")
    return True

def process_onboarding_file(transcript_path, account_id):
    """Process a single onboarding file"""
    print(f"\n📄 Processing onboarding: {account_id}")
    
    # Check if v1 exists
    v1_path = Path(OUTPUT_BASE) / account_id / 'v1' / 'memo.json'
    if not v1_path.exists():
        print(f"❌ No v1 memo found for {account_id}")
        return False
    
    # Read v1 memo
    with open(v1_path, 'r', encoding='utf-8') as f:
        v1_memo = json.load(f)
    
    # Read transcript
    transcript = read_file_content(transcript_path)
    
    # Extract updates
    updates_result = subprocess.run(
        ['python', 'scripts/extract_onboarding.py'],
        input=transcript,
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    if updates_result.returncode != 0:
        print(f"❌ Error extracting updates: {updates_result.stderr}")
        return False
    
    try:
        updates = json.loads(updates_result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Invalid updates JSON: {updates_result.stdout[:200]}")
        return False
    
    # Apply updates
    merge_input = json.dumps({"v1_memo": v1_memo, "updates": updates})
    merge_result = subprocess.run(
        ['python', 'scripts/apply_updates.py'],
        input=merge_input,
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    if merge_result.returncode != 0:
        print(f"❌ Error applying updates: {merge_result.stderr}")
        return False
    
    try:
        v2_memo = json.loads(merge_result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Invalid merged JSON: {merge_result.stdout[:200]}")
        return False
    
    v2_memo['_version'] = 'v2'
    
    # Generate v2 spec
    spec_result = subprocess.run(
        ['python', 'scripts/generate_agent_spec.py'],
        input=json.dumps(v2_memo),
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    if spec_result.returncode != 0:
        print(f"❌ Error generating v2 spec: {spec_result.stderr}")
        return False
    
    try:
        v2_spec = json.loads(spec_result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Invalid v2 spec JSON: {spec_result.stdout[:200]}")
        return False
    
    v2_spec['version'] = 'v2'
    
    # Generate changelog
    diff_input = json.dumps({"v1": v1_memo, "v2": v2_memo, "account_id": account_id})
    diff_result = subprocess.run(
        ['python', 'scripts/diff_memo.py'],
        input=diff_input,
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    
    # Save v2 outputs
    output_dir = Path(OUTPUT_BASE) / account_id / 'v2'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'memo.json', 'w', encoding='utf-8') as f:
        json.dump(v2_memo, f, indent=2)
    
    with open(output_dir / 'agent_spec.json', 'w', encoding='utf-8') as f:
        json.dump(v2_spec, f, indent=2)
    
    with open(output_dir / 'changelog.md', 'w', encoding='utf-8') as f:
        f.write(diff_result.stdout)
    
    # Log task
    log_task(account_id, 'v2', 'updated')
    
    print(f"✅ Completed onboarding: {account_id}")
    return True

def log_task(account_id, stage, status):
    """Append to tasks log"""
    tasks_file = Path('outputs/tasks.json')
    tasks = []
    if tasks_file.exists():
        with open(tasks_file, 'r', encoding='utf-8') as f:
            try:
                tasks = json.load(f)
            except:
                tasks = []
    
    tasks.append({
        "timestamp": datetime.now().isoformat(),
        "account_id": account_id,
        "stage": stage,
        "status": status
    })
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)

def check_ollama():
    """Verify Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if any(m['name'].startswith('llama3.2') for m in models):
                print("✅ Ollama is running with llama3.2:3b")
                return True
            else:
                print("⚠️  Ollama running but llama3.2:3b not found. Run: ollama pull llama3.2:3b")
                return False
    except:
        print("❌ Ollama is not running. Start it first!")
        return False

def main():
    print("=" * 50)
    print("🚀 Clara Automation Pipeline")
    print("=" * 50)
    
    # Check Ollama first
    if not check_ollama():
        print("\nPlease start Ollama and try again")
        return
    
    ensure_folders()
    
    # Process demo files
    demo_files = list(Path(DEMO_FOLDER).glob("*.txt"))
    print(f"\n📁 Found {len(demo_files)} demo files")
    
    demo_success = 0
    for demo_file in demo_files:
        account_id = demo_file.stem  # filename without .txt
        if process_demo_file(demo_file, account_id):
            demo_success += 1
    
    # Process onboarding files
    onboarding_files = list(Path(ONBOARDING_FOLDER).glob("*.txt"))
    print(f"\n📁 Found {len(onboarding_files)} onboarding files")
    
    onboarding_success = 0
    for onboarding_file in onboarding_files:
        account_id = onboarding_file.stem
        if process_onboarding_file(onboarding_file, account_id):
            onboarding_success += 1
    
    print("\n" + "=" * 50)
    print("✨ Pipeline Complete!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"   Demo files processed: {demo_success}/{len(demo_files)}")
    print(f"   Onboarding files processed: {onboarding_success}/{len(onboarding_files)}")
    print(f"\n📁 Outputs saved in: {OUTPUT_BASE}")
    print("\nNext steps:")
    print("1. Check outputs/accounts/ folder for results")
    print("2. Each account has v1/ and v2/ folders")
    print("3. v2/changelog.md shows what changed")
    print("4. Use agent_spec.json to manually configure Retell AI")

if __name__ == "__main__":
    main()