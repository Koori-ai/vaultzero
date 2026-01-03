"""
Quick integration test - KEVS + NVD working together
"""
import asyncio
from tools.kevs_tool import KEVSTool
from tools.nvd_tool import NVDTool


async def main():
    print("🚀 VaultZero 2.0 - Day 2 Integration Test\n")
    
    # Initialize both tools
    kevs_tool = KEVSTool()
    nvd_tool = NVDTool()
    
    # Get weekly KEVS
    print("📊 Fetching KEVS from last 7 days...")
    weekly_kevs = await kevs_tool.get_weekly_kevs()
    print(f"Found {len(weekly_kevs)} new KEVs this week\n")
    
    if weekly_kevs:
        # Enrich with NVD data
        print("🔍 Enriching with NVD CVE details...")
        enriched = await nvd_tool.enrich_kevs(weekly_kevs[:3])  # Just first 3
        
        print(f"\n✅ Enriched {len(enriched)} vulnerabilities!\n")
        
        # Show first enriched vulnerability
        if enriched:
            vuln = enriched[0]
            print("=" * 60)
            print("SAMPLE ENRICHED VULNERABILITY:")
            print("=" * 60)
            print(f"CVE ID: {vuln['cveID']}")
            print(f"Vendor: {vuln['vendorProject']}")
            print(f"Product: {vuln['product']}")
            print(f"KEVS Added: {vuln['dateAdded']}")
            
            if 'nvd_data' in vuln:
                nvd = vuln['nvd_data']
                
                # CVSS Score
                if nvd['cvss_scores']['cvss_v31']:
                    cvss = nvd['cvss_scores']['cvss_v31']
                    print(f"\nCVSS Score: {cvss['baseScore']}")
                    print(f"Severity: {cvss['baseSeverity']}")
                
                # CWE
                if nvd['cwe']:
                    print(f"CWE: {', '.join(nvd['cwe'])}")
                
                # Description
                print(f"\nNVD Description:")
                print(f"{nvd['description'][:200]}...")
                
        print("\n" + "=" * 60)
        print("🎉 Integration successful! KEVS + NVD working together!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())