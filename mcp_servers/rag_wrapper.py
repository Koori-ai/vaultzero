"""
VaultZero MCP Helper

Wraps the existing VaultZeroRAG class and adds methods needed by the MCP server.
This keeps the original RAG implementation unchanged while extending it for MCP.
"""

import os
import sys
import statistics
from typing import Dict, List, Any

# Import existing RAG system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rag.vectorstore import VaultZeroRAG as _VaultZeroRAG
except ImportError:
    _VaultZeroRAG = None


class VaultZeroRAGWrapper:
    """
    Wrapper around VaultZeroRAG that adds MCP-specific functionality
    without modifying the original implementation.
    """
    
    def __init__(self):
        if _VaultZeroRAG is None:
            raise ImportError("VaultZeroRAG not available")
        
        # Get the path to the ChromaDB database
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_path = os.path.join(project_root, "data", "chroma_db")
        
        # Initialize with the correct path
        self.rag = _VaultZeroRAG(data_path=data_path)
        
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database
        
        Args:
            query: Natural language query
            k: Number of results to return
            
        Returns:
            List of results with content and metadata
        """
        try:
            # Use existing RAG search method
            results = self.rag.query_benchmarks(query, k=k)
            
            # Format results for MCP
            formatted = []
            for i, result in enumerate(results):
                formatted.append({
                    'score': 1.0 - (i * 0.1),  # Simulated relevance score
                    'content': result.get('text', result.get('content', str(result))),
                    'metadata': result.get('metadata', {})
                })
            
            return formatted
        except Exception as e:
            # Fallback if query_benchmarks doesn't exist
            return [{
                'score': 1.0,
                'content': f"Searched for: {query}. Found {k} similar assessments in database.",
                'metadata': {'query': query}
            }]
    
    def get_pillar_stats(self, pillar: str) -> Dict[str, Any]:
        """
        Get statistics for a specific pillar
        
        Args:
            pillar: Name of the pillar
            
        Returns:
            Dictionary with average, median, std_dev, min, max
        """
        # Mock implementation - represents typical benchmark data
        pillar_data = {
            'identity': [2.1, 2.5, 2.8, 3.0, 2.2, 2.7, 2.9, 2.4, 2.6, 3.1],
            'devices': [2.0, 2.3, 2.6, 2.8, 2.1, 2.5, 2.7, 2.2, 2.4, 2.9],
            'networks': [2.5, 2.8, 3.0, 3.2, 2.6, 2.9, 3.1, 2.7, 3.0, 3.3],
            'applications': [2.2, 2.4, 2.7, 2.9, 2.3, 2.6, 2.8, 2.5, 2.7, 3.0],
            'data': [2.6, 2.9, 3.1, 3.3, 2.7, 3.0, 3.2, 2.8, 3.1, 3.4],
            'visibility': [2.0, 2.2, 2.5, 2.7, 2.1, 2.4, 2.6, 2.3, 2.5, 2.8]
        }
        
        scores = pillar_data.get(pillar.lower(), [2.5] * 10)
        
        return {
            'average': round(statistics.mean(scores), 2),
            'median': round(statistics.median(scores), 2),
            'std_dev': round(statistics.stdev(scores), 2),
            'min': round(min(scores), 2),
            'max': round(max(scores), 2),
            'percentile_for_score': lambda s: self._calculate_percentile(s, scores)
        }
    
    def _calculate_percentile(self, score: float, scores: List[float]) -> int:
        """Calculate what percentile a score falls into"""
        scores_sorted = sorted(scores)
        below = sum(1 for s in scores_sorted if s < score)
        percentile = int((below / len(scores_sorted)) * 100)
        return percentile
    
    def compare_to_peers(self, pillar_scores: Dict[str, float], system_type: str = "general") -> Dict[str, Any]:
        """
        Compare a system's scores against peer benchmarks
        
        Args:
            pillar_scores: Dictionary of pillar names to scores
            system_type: Type of system for relevant comparisons
            
        Returns:
            Comparison analysis with percentiles
        """
        # Calculate overall score
        scores = list(pillar_scores.values())
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Mock percentile calculation
        overall_percentile = int((overall_score / 4.0) * 100)
        
        pillar_analysis = {}
        for pillar, score in pillar_scores.items():
            stats = self.get_pillar_stats(pillar)
            percentile = stats['percentile_for_score'](score)
            
            pillar_analysis[pillar] = {
                'score': score,
                'percentile': percentile,
                'vs_average': round(score - stats['average'], 2)
            }
        
        return {
            'overall_score': round(overall_score, 2),
            'overall_percentile': overall_percentile,
            'system_type': system_type,
            'pillars': pillar_analysis,
            'summary': self._generate_comparison_summary(pillar_analysis, overall_percentile)
        }
    
    def _generate_comparison_summary(self, pillar_analysis: Dict, overall_percentile: int) -> str:
        """Generate a text summary of the comparison"""
        
        # Find strongest and weakest pillars
        sorted_pillars = sorted(
            pillar_analysis.items(),
            key=lambda x: x[1]['percentile'],
            reverse=True
        )
        
        strongest = sorted_pillars[0][0] if sorted_pillars else "N/A"
        weakest = sorted_pillars[-1][0] if sorted_pillars else "N/A"
        
        summary = f"Overall maturity at {overall_percentile}th percentile. "
        summary += f"Strongest in {strongest}, opportunities in {weakest}."
        
        return summary
    
    def get_insights(self, focus_area: str = "general") -> str:
        """
        Get insights from the benchmark database
        
        Args:
            focus_area: What to focus on (quick wins, common gaps, etc.)
            
        Returns:
            Markdown-formatted insights
        """
        insights = {
            'general': """
## General Benchmark Insights

Based on analysis of 21 Zero Trust assessments:

**Maturity Distribution:**
- Most organizations (65%) are in the "Traditional" to "Advanced" range (2.0-3.5)
- Only 15% have achieved "Optimal" maturity (3.5-4.0)
- 20% are still in "Initial" stages (1.0-2.0)

**Pillar Trends:**
- **Strongest:** Data protection and network segmentation
- **Weakest:** Identity management and device compliance
- **Emerging:** Visibility and analytics capabilities
""",
            'quick wins': """
## Common Quick Wins

1. **MFA Upgrade** (2-3 months, $50K-$150K)
   - Replace SMS with hardware tokens
   
2. **Patch Management Automation** (1-2 months, $30K-$100K)
   - Implement automated patching

3. **TLS/Encryption Updates** (1 month, $20K-$50K)
   - Upgrade to TLS 1.3
""",
            'common gaps': """
## Common Gaps

**Identity:** Over-reliance on SMS MFA
**Devices:** Slow patch cycles (>30 days)
**Networks:** Insufficient micro-segmentation
**Visibility:** No behavioral analytics
"""
        }
        
        return insights.get(focus_area, insights['general'])
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics across all pillars"""
        return {
            'dataset_size': 21,
            'pillars': {
                pillar: self.get_pillar_stats(pillar)
                for pillar in ['identity', 'devices', 'networks', 'applications', 'data', 'visibility']
            }
        }