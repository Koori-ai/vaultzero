"""Quick test script for VaultZero RAG system"""

import sys
sys.path.append('.')

from rag.vectorstore import VaultZeroRAG

DATA_PATH = r"C:\projects\zt-assessment-generator\data\output\zt_synthetic_dataset_complete.json"

def main():
    print("VaultZero RAG System Test")
    print("=" * 60)
    
    rag = VaultZeroRAG(DATA_PATH)
    rag.initialize()
    
    print("\nTesting search...")
    query = "web application handling customer data"
    print(f"\nQuery: '{query}'\n")
    
    results = rag.search_similar_systems(query, k=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['system_id']} - {result['system_type']}")
        print(f"   Maturity: {result['maturity']}")
        print(f"   Score: {result['similarity_score']:.4f}")
        print()
    
    print("Test complete!")

if __name__ == "__main__":
    main()