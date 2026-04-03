import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"📍 {description}")
    print(f"{'='*60}")
    
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"✅ {description} - DONE")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED: {e}")
        return False

def main():
    print("\n" + "🚀"*30)
    print("PLACEMENT CHATBOT - PIPELINE EXECUTION")
    print("🚀"*30)
    
    phases = [
        ("python data_collector.py", "Phase 1: Data Collection"),
        ("python data_cleaner.py", "Phase 2: Data Cleaning"),
        ("python knowledge_base_builder.py", "Phase 3: Knowledge Base Creation"),
        ("python chatbot.py", "Phase 4: Chatbot Testing"),
    ]
    
    for cmd, description in phases:
        if not run_command(cmd, description):
            print(f"\n⚠️  Stopping at {description}")
            return False
    
    print("\n" + "="*60)
    print("✅ ALL PHASES COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n🚀 To start API server, run:")
    print("   python app.py")
    print("\n📝 Then test with:")
    print("   curl http://localhost:5000/health")

if __name__ == "__main__":
    main()
