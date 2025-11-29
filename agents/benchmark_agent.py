"""
Benchmark Agent - Compares user's system against similar systems using RAG
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.vectorstore import VaultZeroRAG

# Load environment variables
load_dotenv()

class BenchmarkAgent:
    def __init__(self):
        """Initialize the Benchmark Agent with Claude API and RAG system"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        
        # Initialize RAG with correct parameters
        data_path = r"C:\projects\zt-assessment-generator\data\output\zt_synthetic_dataset_complete.json"
        persist_dir = "./data/chroma_db"
        
        self.rag = VaultZeroRAG(data_path=data_path, persist_directory=persist_dir)
        self.rag.load_existing_vectorstore()
        
    def find_similar_systems(self, system_description: str, top_k: int = 3):
        """Use RAG to find similar systems"""
        print(f"\n🔍 Finding {top_k} similar systems...")
        results = self.rag.search_similar_systems(system_description, k=top_k)
        
        similar_systems = []
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result['system_id']} - {result['system_type']}")
            print(f"     Maturity: {result['maturity']}")
            print(f"     Similarity: {result['similarity_score']:.4f}")
            
            # Extract just the key info for comparison
            similar_systems.append({
                'system_id': result['system_id'],
                'system_type': result['system_type'],
                'overall_maturity': result['maturity'],
                'similarity_score': result['similarity_score'],
                'content_preview': result['content'][:500]  # First 500 chars
            })
        
        return similar_systems
    
    def compare_to_benchmarks(self, 
                            system_description: str,
                            assessment_results: dict,
                            similar_systems: list):
        """Compare user's system against benchmark systems"""
        
        # Prepare the comparison prompt
        prompt = f"""You are a Zero Trust benchmarking expert. Compare this system against similar peer systems.

USER'S SYSTEM:
Description: {system_description}

Assessment Results:
{json.dumps(assessment_results, indent=2)}

SIMILAR BENCHMARK SYSTEMS:
{json.dumps(similar_systems, indent=2)}

Provide a comprehensive benchmark analysis in JSON format:
{{
    "overall_percentile": <0-100, where user ranks among peers>,
    "pillar_rankings": {{
        "identity": {{"percentile": <0-100>, "vs_peers": "above/at/below average"}},
        "devices": {{"percentile": <0-100>, "vs_peers": "above/at/below average"}},
        "networks": {{"percentile": <0-100>, "vs_peers": "above/at/below average"}},
        "applications": {{"percentile": <0-100>, "vs_peers": "above/at/below average"}},
        "data": {{"percentile": <0-100>, "vs_peers": "above/at/below average"}}
    }},
    "strengths_vs_peers": [
        "Area where user exceeds peer average"
    ],
    "gaps_vs_peers": [
        "Area where user lags behind peers"
    ],
    "peer_best_practices": [
        {{
            "practice": "Best practice from peer systems",
            "system": "Which peer system does this well",
            "implementation": "How they implemented it"
        }}
    ],
    "competitive_position": "brief 2-3 sentence summary of where user stands vs peers"
}}

Be specific and actionable. Focus on meaningful differences."""

        print("\n📊 Running benchmark comparison with Claude API...")
        
        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Claude sometimes wraps JSON in markdown, strip it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        benchmark_results = json.loads(response_text)
        
        return benchmark_results
    
    def run_benchmark(self, system_description: str, assessment_results: dict):
        """Complete benchmarking workflow"""
        
        print("\n" + "="*60)
        print("🎯 VAULTZERO BENCHMARK AGENT")
        print("="*60)
        
        # Step 1: Find similar systems using RAG
        similar_systems = self.find_similar_systems(system_description, top_k=3)
        
        # Step 2: Compare against benchmarks
        benchmark_results = self.compare_to_benchmarks(
            system_description,
            assessment_results,
            similar_systems
        )
        
        # Step 3: Display results
        print("\n" + "="*60)
        print("📊 BENCHMARK RESULTS")
        print("="*60)
        
        print(f"\n🎯 Overall Percentile: {benchmark_results['overall_percentile']}th")
        print(f"   {benchmark_results['competitive_position']}")
        
        print("\n📈 Pillar Rankings vs Peers:")
        for pillar, data in benchmark_results['pillar_rankings'].items():
            print(f"   • {pillar.title()}: {data['percentile']}th percentile ({data['vs_peers']})")
        
        print("\n💪 Strengths vs Peers:")
        for strength in benchmark_results['strengths_vs_peers']:
            print(f"   • {strength}")
        
        print("\n⚠️  Gaps vs Peers:")
        for gap in benchmark_results['gaps_vs_peers']:
            print(f"   • {gap}")
        
        print("\n🌟 Peer Best Practices to Adopt:")
        for practice in benchmark_results['peer_best_practices']:
            print(f"   • {practice['practice']}")
            print(f"     From: {practice['system']}")
            print(f"     How: {practice['implementation']}\n")
        
        return benchmark_results


# Test code
if __name__ == "__main__":
    # GENERIC TEST DATA - For testing only
    test_system = "Cloud-based enterprise SaaS application"
    
    test_assessment = {
        "system_name": "Enterprise Cloud Application",
        "pillars": {
            "identity": {"maturity_level": "INITIAL", "score": 2},
            "devices": {"maturity_level": "ADVANCED", "score": 3},
            "networks": {"maturity_level": "INITIAL", "score": 2},
            "applications": {"maturity_level": "TRADITIONAL", "score": 1},
            "data": {"maturity_level": "INITIAL", "score": 2}
        }
    }
    
    # Run benchmark
    agent = BenchmarkAgent()
    results = agent.run_benchmark(test_system, test_assessment)
    
    # Save results
    with open("benchmark_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Results saved to benchmark_test_results.json")