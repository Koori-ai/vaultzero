"""
KEVS Tool - CISA Known Exploited Vulnerabilities Catalog Integration
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class KEVSTool:
    """
    Tool for querying CISA's Known Exploited Vulnerabilities (KEVS) catalog.
    
    API: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
    Free, public, updated daily by CISA.
    """
    
    KEVS_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    
    def __init__(self):
        self.catalog_cache = None
        self.cache_timestamp = None
        self.cache_ttl = 3600  # Cache for 1 hour
    
    async def get_kevs_catalog(self, use_cache: bool = True) -> Dict:
        """
        Fetch the complete KEVS catalog from CISA.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            Dict containing the full KEVS catalog
        """
        # Check cache
        if use_cache and self.catalog_cache and self.cache_timestamp:
            cache_age = (datetime.now() - self.cache_timestamp).total_seconds()
            if cache_age < self.cache_ttl:
                return self.catalog_cache
        
        # Fetch fresh data
        async with aiohttp.ClientSession() as session:
            async with session.get(self.KEVS_URL) as response:
                if response.status == 200:
                    catalog = await response.json()
                    
                    # Update cache
                    self.catalog_cache = catalog
                    self.cache_timestamp = datetime.now()
                    
                    return catalog
                else:
                    raise Exception(f"Failed to fetch KEVS catalog: HTTP {response.status}")
    
    async def get_vulnerabilities(self) -> List[Dict]:
        """
        Get just the vulnerabilities list from the catalog.
        
        Returns:
            List of vulnerability dictionaries
        """
        catalog = await self.get_kevs_catalog()
        return catalog.get('vulnerabilities', [])
    
    async def get_new_kevs(self, since_date: str) -> List[Dict]:
        """
        Get KEVs added since a specific date.
        
        Args:
            since_date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            List of vulnerabilities added on or after since_date
        """
        vulnerabilities = await self.get_vulnerabilities()
        
        new_kevs = []
        for vuln in vulnerabilities:
            date_added = vuln.get('dateAdded', '')
            if date_added >= since_date:
                new_kevs.append(vuln)
        
        return new_kevs
    
    async def get_weekly_kevs(self) -> List[Dict]:
        """
        Get KEVs added in the last 7 days.
        
        Returns:
            List of vulnerabilities from the past week
        """
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        return await self.get_new_kevs(week_ago)
    
    async def get_daily_kevs(self) -> List[Dict]:
        """
        Get KEVs added today.
        
        Returns:
            List of vulnerabilities added today
        """
        today = datetime.now().strftime('%Y-%m-%d')
        return await self.get_new_kevs(today)
    
    def filter_by_vendor(self, vulnerabilities: List[Dict], vendor: str) -> List[Dict]:
        """
        Filter vulnerabilities by vendor name.
        
        Args:
            vulnerabilities: List of vulnerability dicts
            vendor: Vendor name to filter by (case-insensitive)
            
        Returns:
            Filtered list of vulnerabilities
        """
        vendor_lower = vendor.lower()
        return [
            v for v in vulnerabilities 
            if vendor_lower in v.get('vendorProject', '').lower()
        ]
    
    def filter_by_product(self, vulnerabilities: List[Dict], product: str) -> List[Dict]:
        """
        Filter vulnerabilities by product name.
        
        Args:
            vulnerabilities: List of vulnerability dicts
            product: Product name to filter by (case-insensitive)
            
        Returns:
            Filtered list of vulnerabilities
        """
        product_lower = product.lower()
        return [
            v for v in vulnerabilities 
            if product_lower in v.get('product', '').lower()
        ]
    
    async def get_catalog_stats(self) -> Dict:
        """
        Get statistics about the KEVS catalog.
        
        Returns:
            Dict with catalog statistics
        """
        catalog = await self.get_kevs_catalog()
        vulnerabilities = catalog.get('vulnerabilities', [])
        
        return {
            'total_kevs': len(vulnerabilities),
            'catalog_version': catalog.get('catalogVersion', 'Unknown'),
            'date_released': catalog.get('dateReleased', 'Unknown'),
            'title': catalog.get('title', 'Unknown'),
            'count': catalog.get('count', 0)
        }


# Example usage
async def main():
    """Example usage of KEVSTool"""
    tool = KEVSTool()
    
    # Get catalog stats
    print("Fetching KEVS catalog stats...")
    stats = await tool.get_catalog_stats()
    print(f"\nCatalog Statistics:")
    print(f"  Total KEVs: {stats['total_kevs']}")
    print(f"  Version: {stats['catalog_version']}")
    print(f"  Released: {stats['date_released']}")
    
    # Get weekly KEVs
    print("\nFetching KEVs from last 7 days...")
    weekly_kevs = await tool.get_weekly_kevs()
    print(f"Found {len(weekly_kevs)} new KEVs this week")
    
    if weekly_kevs:
        print("\nMost recent KEV:")
        latest = weekly_kevs[0]
        print(f"  CVE: {latest.get('cveID')}")
        print(f"  Vendor: {latest.get('vendorProject')}")
        print(f"  Product: {latest.get('product')}")
        print(f"  Added: {latest.get('dateAdded')}")
        print(f"  Description: {latest.get('shortDescription', '')[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())