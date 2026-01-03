"""
NVD Tool - National Vulnerability Database API Integration
"""

import aiohttp
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NVDTool:
    """
    Tool for querying NIST's National Vulnerability Database (NVD).
    
    API: https://services.nvd.nist.gov/rest/json/cves/2.0
    Requires free API key for better rate limits (5 requests/sec vs 0.6/sec)
    """
    
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NVD Tool.
        
        Args:
            api_key: NVD API key. If not provided, reads from NVD_API_KEY env var
        """
        self.api_key = api_key or os.getenv('NVD_API_KEY')
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
        # Rate limiting
        self.rate_limit = 5 if self.api_key else 0.6  # requests per second
        self.last_request_time = None
    
    async def _wait_for_rate_limit(self):
        """Enforce rate limiting between API requests"""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            min_interval = 1.0 / self.rate_limit
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = datetime.now()
    
    async def get_cve(self, cve_id: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get details for a specific CVE.
        
        Args:
            cve_id: CVE identifier (e.g., "CVE-2024-12345")
            use_cache: Whether to use cached data if available
            
        Returns:
            Dict with CVE details or None if not found
        """
        # Check cache
        if use_cache and cve_id in self.cache:
            cached_data, cache_time = self.cache[cve_id]
            cache_age = (datetime.now() - cache_time).total_seconds()
            
            if cache_age < self.cache_ttl:
                return cached_data
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        # Prepare headers
        headers = {}
        if self.api_key:
            headers['apiKey'] = self.api_key
        
        # Make API request
        params = {'cveId': cve_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract the CVE from response
                    vulnerabilities = data.get('vulnerabilities', [])
                    if vulnerabilities:
                        cve_data = vulnerabilities[0].get('cve', {})
                        
                        # Cache it
                        self.cache[cve_id] = (cve_data, datetime.now())
                        
                        return cve_data
                    else:
                        return None
                elif response.status == 404:
                    return None
                else:
                    raise Exception(f"NVD API error: HTTP {response.status}")
    
    def extract_cvss_scores(self, cve_data: Dict) -> Dict:
        """
        Extract CVSS scores from CVE data.
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            Dict with CVSS v3.1, v3.0, and v2.0 scores
        """
        scores = {
            'cvss_v31': None,
            'cvss_v30': None,
            'cvss_v2': None
        }
        
        metrics = cve_data.get('metrics', {})
        
        # CVSS v3.1
        if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
            cvss_v31 = metrics['cvssMetricV31'][0]['cvssData']
            scores['cvss_v31'] = {
                'baseScore': cvss_v31.get('baseScore'),
                'baseSeverity': cvss_v31.get('baseSeverity'),
                'vectorString': cvss_v31.get('vectorString'),
                'exploitabilityScore': metrics['cvssMetricV31'][0].get('exploitabilityScore'),
                'impactScore': metrics['cvssMetricV31'][0].get('impactScore')
            }
        
        # CVSS v3.0
        if 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
            cvss_v30 = metrics['cvssMetricV30'][0]['cvssData']
            scores['cvss_v30'] = {
                'baseScore': cvss_v30.get('baseScore'),
                'baseSeverity': cvss_v30.get('baseSeverity'),
                'vectorString': cvss_v30.get('vectorString')
            }
        
        # CVSS v2.0
        if 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
            cvss_v2 = metrics['cvssMetricV2'][0]['cvssData']
            scores['cvss_v2'] = {
                'baseScore': cvss_v2.get('baseScore'),
                'vectorString': cvss_v2.get('vectorString')
            }
        
        return scores
    
    def extract_cwe(self, cve_data: Dict) -> List[str]:
        """
        Extract CWE (Common Weakness Enumeration) classifications.
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            List of CWE IDs (e.g., ["CWE-79", "CWE-89"])
        """
        cwes = []
        
        weaknesses = cve_data.get('weaknesses', [])
        for weakness in weaknesses:
            descriptions = weakness.get('description', [])
            for desc in descriptions:
                cwe_id = desc.get('value')
                if cwe_id and cwe_id.startswith('CWE-'):
                    cwes.append(cwe_id)
        
        return list(set(cwes))  # Remove duplicates
    
    def extract_references(self, cve_data: Dict) -> List[Dict]:
        """
        Extract references (advisories, patches, etc.).
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            List of reference dicts with url and tags
        """
        references = []
        
        refs = cve_data.get('references', [])
        for ref in refs:
            references.append({
                'url': ref.get('url'),
                'source': ref.get('source'),
                'tags': ref.get('tags', [])
            })
        
        return references
    
    def extract_description(self, cve_data: Dict) -> str:
        """
        Extract English description.
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            Description string
        """
        descriptions = cve_data.get('descriptions', [])
        
        for desc in descriptions:
            if desc.get('lang') == 'en':
                return desc.get('value', '')
        
        return ''
    
    def get_published_date(self, cve_data: Dict) -> str:
        """
        Get CVE published date.
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            ISO format date string
        """
        return cve_data.get('published', '')
    
    def get_last_modified_date(self, cve_data: Dict) -> str:
        """
        Get CVE last modified date.
        
        Args:
            cve_data: CVE data from NVD API
            
        Returns:
            ISO format date string
        """
        return cve_data.get('lastModified', '')
    
    async def enrich_kevs(self, kevs_list: List[Dict]) -> List[Dict]:
        """
        Enrich KEVS vulnerabilities with NVD CVE details.
        
        Args:
            kevs_list: List of KEVS vulnerabilities
            
        Returns:
            List of enriched vulnerabilities with CVE details
        """
        enriched = []
        
        for kev in kevs_list:
            cve_id = kev.get('cveID')
            
            if cve_id:
                # Get CVE details from NVD
                cve_data = await self.get_cve(cve_id)
                
                if cve_data:
                    # Enrich the KEVS entry
                    enriched_kev = kev.copy()
                    enriched_kev['nvd_data'] = {
                        'cvss_scores': self.extract_cvss_scores(cve_data),
                        'cwe': self.extract_cwe(cve_data),
                        'references': self.extract_references(cve_data),
                        'description': self.extract_description(cve_data),
                        'published': self.get_published_date(cve_data),
                        'lastModified': self.get_last_modified_date(cve_data)
                    }
                    enriched.append(enriched_kev)
                else:
                    # CVE not found in NVD, keep original
                    enriched.append(kev)
            else:
                enriched.append(kev)
        
        return enriched
    
    async def get_severity_summary(self, cve_id: str) -> Dict:
        """
        Get a quick severity summary for a CVE.
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            Dict with severity info
        """
        cve_data = await self.get_cve(cve_id)
        
        if not cve_data:
            return {'error': 'CVE not found'}
        
        scores = self.extract_cvss_scores(cve_data)
        
        # Prefer CVSS v3.1, fallback to v3.0, then v2
        severity = 'UNKNOWN'
        score = None
        
        if scores['cvss_v31']:
            severity = scores['cvss_v31']['baseSeverity']
            score = scores['cvss_v31']['baseScore']
        elif scores['cvss_v30']:
            severity = scores['cvss_v30']['baseSeverity']
            score = scores['cvss_v30']['baseScore']
        elif scores['cvss_v2']:
            score = scores['cvss_v2']['baseScore']
            # CVSS v2 doesn't have severity labels, calculate it
            if score >= 7.0:
                severity = 'HIGH'
            elif score >= 4.0:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
        
        return {
            'cve_id': cve_id,
            'severity': severity,
            'score': score,
            'cwe': self.extract_cwe(cve_data),
            'description': self.extract_description(cve_data)[:200] + '...'  # Truncate
        }


# Example usage
async def main():
    """Example usage of NVDTool"""
    tool = NVDTool()
    
    # Test with a known CVE
    print("Fetching CVE-2021-44228 (Log4Shell)...")
    cve_data = await tool.get_cve('CVE-2021-44228')
    
    if cve_data:
        print("\n✅ CVE Found!")
        
        # Extract details
        scores = tool.extract_cvss_scores(cve_data)
        cwes = tool.extract_cwe(cve_data)
        description = tool.extract_description(cve_data)
        
        print(f"\nDescription: {description[:200]}...")
        
        if scores['cvss_v31']:
            print(f"\nCVSS v3.1 Score: {scores['cvss_v31']['baseScore']}")
            print(f"Severity: {scores['cvss_v31']['baseSeverity']}")
        
        print(f"\nCWE Classifications: {', '.join(cwes)}")
        
        # Quick severity summary
        print("\n" + "="*50)
        print("Quick Severity Summary:")
        summary = await tool.get_severity_summary('CVE-2021-44228')
        print(f"  Severity: {summary['severity']}")
        print(f"  Score: {summary['score']}")
        print(f"  CWE: {', '.join(summary['cwe'])}")
    else:
        print("❌ CVE not found")


if __name__ == "__main__":
    asyncio.run(main())