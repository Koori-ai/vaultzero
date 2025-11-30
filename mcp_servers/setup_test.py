"""
VaultZero MCP Setup and Test Script
"""

import sys
import os
import json

def check_mcp_installed():
    """Check if MCP package is installed"""
    print("\n📦 Checking MCP package...")
    try:
        import mcp
        print("   ✅ MCP package installed")
        return True
    except ImportError:
        print("   ❌ MCP package not found")
        print("   Install with: pip install mcp")
        return False

def check_project_structure():
    """Verify project structure is correct"""
    print("\n📁 Checking project structure...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    required_paths = [
        ("rag/vectorstore.py", "RAG system"),
        ("data/chroma_db", "ChromaDB database"),
        ("mcp_servers/benchmark_server.py", "MCP server"),
        ("mcp_servers/rag_wrapper.py", "RAG wrapper")
    ]
    
    all_good = True
    for path, desc in required_paths:
        full_path = os.path.join(project_root, path)
        if os.path.exists(full_path):
            print(f"   ✅ {desc}: {path}")
        else:
            print(f"   ❌ {desc} not found: {path}")
            all_good = False
    
    return all_good

def test_rag_wrapper():
    """Test if RAG wrapper can be imported"""
    print("\n🔧 Testing RAG wrapper...")
    
    try:
        sys.path.append(os.path.dirname(__file__))
        from rag_wrapper import VaultZeroRAGWrapper
        
        wrapper = VaultZeroRAGWrapper()
        print("   ✅ RAG wrapper initialized successfully")
        
        stats = wrapper.get_pillar_stats("identity")
        print(f"   ✅ Sample query successful: Identity avg = {stats['average']}")
        
        return True
    except Exception as e:
        print(f"   ❌ RAG wrapper error: {str(e)}")
        return False

def generate_claude_config():
    """Generate Claude Desktop configuration"""
    print("\n📝 Generating Claude Desktop configuration...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    benchmark_server_path = os.path.join(current_dir, "benchmark_server.py")
    
    benchmark_server_path = benchmark_server_path.replace("\\", "\\\\")
    project_root = project_root.replace("\\", "\\\\")
    
    config = {
        "mcpServers": {
            "vaultzero-benchmark": {
                "command": "python",
                "args": [benchmark_server_path],
                "env": {
                    "PYTHONPATH": project_root
                }
            }
        }
    }
    
    config_path = os.path.join(current_dir, "claude_desktop_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"   ✅ Configuration saved to: {config_path}")
    
    print("\n📋 To use with Claude Desktop:")
    print("\n1. Find your Claude config file:")
    print("   Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    
    print("\n2. Add this to your config:")
    print(json.dumps(config, indent=2))
    
    print("\n3. Restart Claude Desktop")
    
    return True

def main():
    """Run all checks and setup"""
    print("=" * 60)
    print("VaultZero MCP Setup & Test")
    print("=" * 60)
    
    checks = [
        ("MCP Package", check_mcp_installed),
        ("Project Structure", check_project_structure),
        ("RAG Wrapper", test_rag_wrapper),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    if all_passed:
        print("\n" + "=" * 60)
        print("✅ All checks passed!")
        print("=" * 60)
        
        generate_claude_config()
        
        print("\n🎉 Setup complete! Your MCP server is ready to use.")
        print("\n📚 Next steps:")
        print("   1. Add configuration to Claude Desktop (see above)")
        print("   2. Restart Claude Desktop app")
        print("   3. Try: 'Use vaultzero-benchmark to query identity stats'")
        
    else:
        print("\n" + "=" * 60)
        print("⚠️  Some checks failed - please fix the issues above")
        print("=" * 60)

if __name__ == "__main__":
    main()