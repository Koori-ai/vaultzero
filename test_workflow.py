"""
Test VaultZero AI Agent Workflow
Runs complete assessment with the 3 test documents
"""
import asyncio
import os
from orchestrator import VaultZeroOrchestrator

async def run_test_assessment():
    print("=" * 60)
    print("🚀 VaultZero v2.0 - AI Agent Workflow Test")
    print("=" * 60)
    print()
    
    # Test files
    test_files = [
        "test_network.txt",
        "test_policy.txt",
        "test_inventory.txt"
    ]
    
    # Verify files exist
    print("📁 Checking test files...")
    for filename in test_files:
        if os.path.exists(filename):
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ Missing: {filename}")
            return
    
    print()
    print("🤖 Initializing AI agents...")
    
    # Create orchestrator
    orchestrator = VaultZeroOrchestrator()
    
    print("✅ Orchestrator ready")
    print()
    print("=" * 60)
    print("🔄 Starting Assessment Workflow...")
    print("=" * 60)
    print()
    
    try:
        # Run the assessment!
        result = await orchestrator.run_assessment(test_files, mode='ai')
        
        # Display results
        print()
        print("=" * 60)
        print("✅ ASSESSMENT COMPLETE!")
        print("=" * 60)
        print()
        print(f"📊 Overall Maturity: {result['overall_maturity_level']}")
        print(f"   Score: {result['overall_maturity_score']}/5.0")
        print()
        print(f"📋 Compliance: {result['compliance_percentage']}%")
        print(f"   Status: {result['compliance_status']}")
        print()
        print(f"📄 Report Generated: {result['report_filename']}")
        print(f"📁 Location: {result['report_path']}")
        print()
        print("=" * 60)
        print()
        print("🎯 Zero Trust Pillar Scores:")
        for pillar, score in result['zt_scores'].items():
            print(f"   {pillar:30s} {score}/5.0")
        print()
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print()
        print("❌ ERROR:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print()
    print("Make sure ANTHROPIC_API_KEY is set!")
    print()
    asyncio.run(run_test_assessment())