"""
Test suite for KEVS Tool
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from tools.kevs_tool import KEVSTool


@pytest.fixture
def kevs_tool():
    """Fixture to create a KEVSTool instance for each test"""
    return KEVSTool()


@pytest.mark.asyncio
async def test_get_kevs_catalog(kevs_tool):
    """Test fetching the complete KEVS catalog"""
    catalog = await kevs_tool.get_kevs_catalog()
    
    # Verify catalog structure
    assert catalog is not None
    assert 'vulnerabilities' in catalog
    assert 'catalogVersion' in catalog
    assert 'dateReleased' in catalog
    assert 'title' in catalog
    assert 'count' in catalog
    
    # Verify vulnerabilities is a list
    assert isinstance(catalog['vulnerabilities'], list)
    assert len(catalog['vulnerabilities']) > 0


@pytest.mark.asyncio
async def test_get_vulnerabilities(kevs_tool):
    """Test getting just the vulnerabilities list"""
    vulnerabilities = await kevs_tool.get_vulnerabilities()
    
    assert isinstance(vulnerabilities, list)
    assert len(vulnerabilities) > 0
    
    # Check first vulnerability has expected fields
    first_vuln = vulnerabilities[0]
    assert 'cveID' in first_vuln
    assert 'vendorProject' in first_vuln
    assert 'product' in first_vuln
    assert 'dateAdded' in first_vuln


@pytest.mark.asyncio
async def test_cache_functionality(kevs_tool):
    """Test that caching works correctly"""
    # First call - should fetch from API
    catalog1 = await kevs_tool.get_kevs_catalog(use_cache=True)
    timestamp1 = kevs_tool.cache_timestamp
    
    # Wait a tiny bit
    await asyncio.sleep(0.1)
    
    # Second call - should use cache
    catalog2 = await kevs_tool.get_kevs_catalog(use_cache=True)
    timestamp2 = kevs_tool.cache_timestamp
    
    # Timestamps should be the same (using cache)
    assert timestamp1 == timestamp2
    assert catalog1 == catalog2
    
    # Force fresh fetch
    catalog3 = await kevs_tool.get_kevs_catalog(use_cache=False)
    timestamp3 = kevs_tool.cache_timestamp
    
    # Timestamp should be updated
    assert timestamp3 > timestamp1


@pytest.mark.asyncio
async def test_get_weekly_kevs(kevs_tool):
    """Test getting KEVs from the last 7 days"""
    weekly_kevs = await kevs_tool.get_weekly_kevs()
    
    assert isinstance(weekly_kevs, list)
    # Can be empty if no KEVs added this week
    
    if weekly_kevs:
        # Verify all returned KEVs are within the last 7 days
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        for vuln in weekly_kevs:
            assert vuln['dateAdded'] >= week_ago


@pytest.mark.asyncio
async def test_get_daily_kevs(kevs_tool):
    """Test getting KEVs added today"""
    daily_kevs = await kevs_tool.get_daily_kevs()
    
    assert isinstance(daily_kevs, list)
    # Can be empty if no KEVs added today
    
    if daily_kevs:
        today = datetime.now().strftime('%Y-%m-%d')
        for vuln in daily_kevs:
            assert vuln['dateAdded'] == today


@pytest.mark.asyncio
async def test_get_new_kevs_specific_date(kevs_tool):
    """Test getting KEVs since a specific date"""
    # Get KEVs from the last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_kevs = await kevs_tool.get_new_kevs(thirty_days_ago)
    
    assert isinstance(new_kevs, list)
    assert len(new_kevs) > 0  # Should have some KEVs in 30 days
    
    # Verify all are from the specified date or later
    for vuln in new_kevs:
        assert vuln['dateAdded'] >= thirty_days_ago


@pytest.mark.asyncio
async def test_filter_by_vendor(kevs_tool):
    """Test filtering vulnerabilities by vendor"""
    vulnerabilities = await kevs_tool.get_vulnerabilities()
    
    # Get a vendor name from the first vulnerability
    if vulnerabilities:
        test_vendor = vulnerabilities[0]['vendorProject']
        
        # Filter by that vendor
        filtered = kevs_tool.filter_by_vendor(vulnerabilities, test_vendor)
        
        assert isinstance(filtered, list)
        assert len(filtered) > 0
        
        # Verify all results match the vendor
        for vuln in filtered:
            assert test_vendor.lower() in vuln['vendorProject'].lower()


@pytest.mark.asyncio
async def test_filter_by_product(kevs_tool):
    """Test filtering vulnerabilities by product"""
    vulnerabilities = await kevs_tool.get_vulnerabilities()
    
    # Get a product name from the first vulnerability
    if vulnerabilities:
        test_product = vulnerabilities[0]['product']
        
        # Filter by that product
        filtered = kevs_tool.filter_by_product(vulnerabilities, test_product)
        
        assert isinstance(filtered, list)
        assert len(filtered) > 0
        
        # Verify all results match the product
        for vuln in filtered:
            assert test_product.lower() in vuln['product'].lower()


@pytest.mark.asyncio
async def test_filter_case_insensitive(kevs_tool):
    """Test that filtering is case-insensitive"""
    vulnerabilities = await kevs_tool.get_vulnerabilities()
    
    if vulnerabilities:
        vendor = vulnerabilities[0]['vendorProject']
        
        # Filter with different cases
        filtered_lower = kevs_tool.filter_by_vendor(vulnerabilities, vendor.lower())
        filtered_upper = kevs_tool.filter_by_vendor(vulnerabilities, vendor.upper())
        filtered_mixed = kevs_tool.filter_by_vendor(vulnerabilities, vendor)
        
        # All should return the same results
        assert len(filtered_lower) == len(filtered_upper)
        assert len(filtered_lower) == len(filtered_mixed)


@pytest.mark.asyncio
async def test_get_catalog_stats(kevs_tool):
    """Test getting catalog statistics"""
    stats = await kevs_tool.get_catalog_stats()
    
    assert isinstance(stats, dict)
    assert 'total_kevs' in stats
    assert 'catalog_version' in stats
    assert 'date_released' in stats
    assert 'title' in stats
    assert 'count' in stats
    
    # Verify counts match
    assert stats['total_kevs'] == stats['count']
    assert stats['total_kevs'] > 0


@pytest.mark.asyncio
async def test_vulnerability_structure(kevs_tool):
    """Test that vulnerabilities have the expected structure"""
    vulnerabilities = await kevs_tool.get_vulnerabilities()
    
    required_fields = [
        'cveID',
        'vendorProject',
        'product',
        'vulnerabilityName',
        'dateAdded',
        'shortDescription',
        'requiredAction',
        'dueDate'
    ]
    
    # Check first few vulnerabilities
    for vuln in vulnerabilities[:5]:
        for field in required_fields:
            assert field in vuln, f"Missing field: {field}"
            assert vuln[field] is not None, f"Field {field} is None"


def test_kevs_url_constant():
    """Test that the KEVS URL is correctly set"""
    assert KEVSTool.KEVS_URL == "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def test_cache_ttl_default():
    """Test that cache TTL is set to 1 hour by default"""
    tool = KEVSTool()
    assert tool.cache_ttl == 3600  # 1 hour in seconds