"""
VaultZero Benchmark MCP Server

This MCP server exposes the Zero Trust benchmark database (ChromaDB) 
as tools and resources that can be used by Claude and other MCP clients.

Dataset: Reply2susi/zero-trust-maturity-assessments (HuggingFace)
Contains: 21 synthetic Zero Trust maturity assessments
"""

import asyncio
import json
import os
import sys
from typing import Any

# Configure UTF-8 encoding for Windows compatibility
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path to import VaultZero modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
)

# Import the RAG wrapper
try:
    from rag_wrapper import VaultZeroRAGWrapper
except ImportError:
    print("Warning: Could not import VaultZeroRAGWrapper. Make sure rag_wrapper.py is accessible.", file=sys.stderr)
    VaultZeroRAGWrapper = None

# Initialize MCP Server
app = Server("vaultzero-benchmark")

# Initialize RAG system (will be done on first tool call)
_rag_instance = None

def clean_text(text: str) -> str:
    """Remove problematic Unicode characters for Windows compatibility"""
    if not isinstance(text, str):
        return str(text)
    # Replace common problematic characters
    text = text.encode('ascii', errors='replace').decode('ascii')
    return text

def get_rag():
    """Lazy initialization of RAG wrapper"""
    global _rag_instance
    if _rag_instance is None and VaultZeroRAGWrapper is not None:
        _rag_instance = VaultZeroRAGWrapper()
    return _rag_instance


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for querying Zero Trust benchmarks"""
    return [
        Tool(
            name="query_zt_benchmarks",
            description=(
                "Query the Zero Trust benchmark database to find similar systems "
                "and compare maturity scores. Uses RAG (Retrieval Augmented Generation) "
                "over 21 real Zero Trust assessments from various organizations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about Zero Trust implementations (e.g., 'healthcare systems with strong identity controls')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of similar assessments to retrieve (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_pillar_statistics",
            description=(
                "Get statistical analysis of Zero Trust pillar scores across "
                "all assessments in the benchmark database. Returns percentile "
                "rankings and average scores for a specific pillar."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar": {
                        "type": "string",
                        "enum": ["identity", "devices", "networks", "applications", "data", "visibility"],
                        "description": "Zero Trust pillar to analyze"
                    },
                    "score": {
                        "type": "number",
                        "description": "Optional: Compare this score against the benchmark (1.0-4.0)",
                        "minimum": 1.0,
                        "maximum": 4.0
                    }
                },
                "required": ["pillar"]
            }
        ),
        Tool(
            name="compare_system_to_peers",
            description=(
                "Compare a system's Zero Trust maturity scores against peer "
                "organizations in the benchmark database. Returns percentile "
                "rankings for each pillar and overall positioning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar_scores": {
                        "type": "object",
                        "description": "Maturity scores for each pillar (1.0-4.0 scale)",
                        "properties": {
                            "identity": {"type": "number", "minimum": 1.0, "maximum": 4.0},
                            "devices": {"type": "number", "minimum": 1.0, "maximum": 4.0},
                            "networks": {"type": "number", "minimum": 1.0, "maximum": 4.0},
                            "applications": {"type": "number", "minimum": 1.0, "maximum": 4.0},
                            "data": {"type": "number", "minimum": 1.0, "maximum": 4.0},
                            "visibility": {"type": "number", "minimum": 1.0, "maximum": 4.0}
                        }
                    },
                    "system_type": {
                        "type": "string",
                        "description": "Optional: Type of system for more relevant comparisons (e.g., 'healthcare', 'financial', 'government')"
                    }
                },
                "required": ["pillar_scores"]
            }
        ),
        Tool(
            name="get_benchmark_insights",
            description=(
                "Get insights and trends from the Zero Trust benchmark database. "
                "Identifies common patterns, best practices, and typical maturity "
                "distributions across all pillars."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "focus_area": {
                        "type": "string",
                        "description": "Optional: Focus on specific aspect (e.g., 'quick wins', 'common gaps', 'investment patterns')"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    rag = get_rag()
    if rag is None:
        return [TextContent(
            type="text",
            text="Error: VaultZero RAG system not available. Make sure ChromaDB is initialized."
        )]
    
    try:
        if name == "query_zt_benchmarks":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            
            # Query the vector database
            results = rag.search(query, k=top_k)
            
            # Format results with clean text
            response = "Zero Trust Benchmark Query Results\n\n"
            response += f"Query: {clean_text(query)}\n\n"
            response += f"Top {len(results)} Similar Assessments:\n\n"
            
            for i, result in enumerate(results, 1):
                response += f"{i}. Assessment\n"
                response += f"Similarity Score: {result.get('score', 'N/A')}\n"
                content = clean_text(result.get('content', 'No content available'))
                response += f"Content: {content}\n\n"
                if 'metadata' in result:
                    metadata_str = json.dumps(result['metadata'], indent=2)
                    response += f"Metadata: {clean_text(metadata_str)}\n\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_pillar_statistics":
            pillar = arguments.get("pillar")
            score = arguments.get("score")
            
            # Get statistics from RAG system
            stats = rag.get_pillar_stats(pillar)
            
            response = f"{pillar.title()} Pillar Statistics\n\n"
            response += f"Average Score: {stats.get('average', 'N/A')}\n"
            response += f"Median Score: {stats.get('median', 'N/A')}\n"
            response += f"Standard Deviation: {stats.get('std_dev', 'N/A')}\n"
            response += f"Range: {stats.get('min', 'N/A')} - {stats.get('max', 'N/A')}\n\n"
            
            if score:
                percentile = stats.get('percentile_for_score')(score)
                response += f"\nYour Score ({score}): {percentile}th percentile\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "compare_system_to_peers":
            pillar_scores = arguments.get("pillar_scores", {})
            system_type = arguments.get("system_type", "general")
            
            # Compare against benchmark
            comparison = rag.compare_to_peers(pillar_scores, system_type)
            
            response = "Peer Comparison Analysis\n\n"
            response += f"System Type: {system_type}\n\n"
            response += "Overall Maturity\n"
            response += f"Score: {comparison.get('overall_score', 'N/A')}/4.0\n"
            response += f"Percentile: {comparison.get('overall_percentile', 'N/A')}th\n\n"
            
            response += "Pillar-by-Pillar Rankings\n\n"
            for pillar, data in comparison.get('pillars', {}).items():
                response += f"{pillar.title()}: {data.get('percentile', 'N/A')}th percentile "
                response += f"(Score: {data.get('score', 'N/A')}/4.0)\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_benchmark_insights":
            focus_area = arguments.get("focus_area", "general")
            
            insights = rag.get_insights(focus_area)
            insights_clean = clean_text(insights)
            
            response = "Zero Trust Benchmark Insights\n\n"
            response += f"Focus Area: {focus_area}\n\n"
            response += insights_clean
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        error_msg = clean_text(str(e))
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {error_msg}"
        )]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources (datasets, documentation)"""
    return [
        Resource(
            uri="dataset://vaultzero/benchmarks",
            name="Zero Trust Benchmark Dataset",
            mimeType="application/json",
            description="21 synthetic Zero Trust maturity assessments from HuggingFace (Reply2susi/zero-trust-maturity-assessments)"
        ),
        Resource(
            uri="docs://vaultzero/methodology",
            name="VaultZero Assessment Methodology",
            mimeType="text/markdown",
            description="Documentation on how Zero Trust maturity assessments are scored and benchmarked"
        ),
        Resource(
            uri="stats://vaultzero/distribution",
            name="Benchmark Distribution Statistics",
            mimeType="application/json",
            description="Statistical distribution of maturity scores across all pillars in the benchmark database"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""
    
    if uri == "dataset://vaultzero/benchmarks":
        return json.dumps({
            "source": "HuggingFace: Reply2susi/zero-trust-maturity-assessments",
            "size": 21,
            "pillars": ["identity", "devices", "networks", "applications", "data", "visibility"],
            "maturity_scale": "1.0 (Initial) to 4.0 (Optimal)"
        }, indent=2)
    
    elif uri == "docs://vaultzero/methodology":
        return """VaultZero Assessment Methodology

Maturity Scale:
- 1.0 - Initial: Ad-hoc processes
- 2.0 - Traditional: Basic security controls
- 3.0 - Advanced: Mature Zero Trust
- 4.0 - Optimal: Industry-leading

Six Pillars:
1. Identity
2. Devices
3. Networks
4. Applications
5. Data
6. Visibility & Analytics
"""
    
    elif uri == "stats://vaultzero/distribution":
        rag = get_rag()
        if rag:
            stats = rag.get_all_stats()
            return json.dumps(stats, indent=2)
        return json.dumps({"error": "RAG system not available"})
    
    else:
        return f"Error: Resource not found: {uri}"


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())