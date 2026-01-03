"""
Test suite for NVD Tool
"""

import pytest
import asyncio
import os
from tools.nvd_tool import NVDTool


@pytest.fixture
def nvd_tool():
    """Fixture to create an NVDTool instance for each test"""
    return NVDTool()


@pytest.mark.asyncio
async def test_get_cve_log4shell(nvd_tool):
    """Test fetching a well-known CVE (Log4Shell)"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    assert 'id' in cve_data
    assert cve_data['id'] == 'CVE-2021-44228'
    assert 'descriptions' in cve_data
    assert 'metrics' in cve_data


@pytest.mark.asyncio
async def test_get_cve_not_found(nvd_tool):
    """Test fetching a non-existent CVE"""
    cve_data = await nvd_tool.get_cve('CVE-9999-99999')
    
    assert cve_data is None


@pytest.mark.asyncio
async def test_cache_functionality(nvd_tool):
    """Test that caching works correctly"""
    cve_id = 'CVE-2021-44228'
    
    # First call - should fetch from API
    cve_data1 = await nvd_tool.get_cve(cve_id, use_cache=True)
    assert cve_id in nvd_tool.cache
    
    # Second call - should use cache (will be faster)
    cve_data2 = await nvd_tool.get_cve(cve_id, use_cache=True)
    
    # Should be the same data
    assert cve_data1 == cve_data2
    
    # Force fresh fetch
    cve_data3 = await nvd_tool.get_cve(cve_id, use_cache=False)
    assert cve_data3 is not None


@pytest.mark.asyncio
async def test_extract_cvss_scores(nvd_tool):
    """Test extracting CVSS scores from CVE data"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    scores = nvd_tool.extract_cvss_scores(cve_data)
    
    assert isinstance(scores, dict)
    assert 'cvss_v31' in scores
    assert 'cvss_v30' in scores
    assert 'cvss_v2' in scores
    
    # Log4Shell should have CVSS v3.1 score
    if scores['cvss_v31']:
        assert 'baseScore' in scores['cvss_v31']
        assert 'baseSeverity' in scores['cvss_v31']
        assert scores['cvss_v31']['baseScore'] >= 0
        assert scores['cvss_v31']['baseScore'] <= 10


@pytest.mark.asyncio
async def test_extract_cwe(nvd_tool):
    """Test extracting CWE classifications"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    cwes = nvd_tool.extract_cwe(cve_data)
    
    assert isinstance(cwes, list)
    # Log4Shell has CWE classifications
    assert len(cwes) > 0
    
    # Check format
    for cwe in cwes:
        assert cwe.startswith('CWE-')


@pytest.mark.asyncio
async def test_extract_references(nvd_tool):
    """Test extracting references"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    references = nvd_tool.extract_references(cve_data)
    
    assert isinstance(references, list)
    assert len(references) > 0
    
    # Check first reference structure
    first_ref = references[0]
    assert 'url' in first_ref
    assert 'source' in first_ref
    assert 'tags' in first_ref
    assert isinstance(first_ref['tags'], list)


@pytest.mark.asyncio
async def test_extract_description(nvd_tool):
    """Test extracting English description"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    description = nvd_tool.extract_description(cve_data)
    
    assert isinstance(description, str)
    assert len(description) > 0
    # Log4Shell description should mention Apache or Log4j
    assert 'Apache' in description or 'Log4j' in description or 'log4j' in description


@pytest.mark.asyncio
async def test_get_published_date(nvd_tool):
    """Test getting published date"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    published = nvd_tool.get_published_date(cve_data)
    
    assert isinstance(published, str)
    assert len(published) > 0
    # Should be ISO format date
    assert 'T' in published  # ISO 8601 format


@pytest.mark.asyncio
async def test_get_last_modified_date(nvd_tool):
    """Test getting last modified date"""
    cve_data = await nvd_tool.get_cve('CVE-2021-44228')
    
    assert cve_data is not None
    
    last_modified = nvd_tool.get_last_modified_date(cve_data)
    
    assert isinstance(last_modified, str)
    assert len(last_modified) > 0
    assert 'T' in last_modified


@pytest.mark.asyncio
async def test_get_severity_summary(nvd_tool):
    """Test getting quick severity summary"""
    summary = await nvd_tool.get_severity_summary('CVE-2021-44228')
    
    assert isinstance(summary, dict)
    assert 'cve_id' in summary
    assert 'severity' in summary
    assert 'score' in summary
    assert 'cwe' in summary
    assert 'description' in summary
    
    assert summary['cve_id'] == 'CVE-2021-44228'
    assert summary['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    assert summary['score'] is not None
    assert isinstance(summary['cwe'], list)


@pytest.mark.asyncio
async def test_get_severity_summary_not_found(nvd_tool):
    """Test severity summary for non-existent CVE"""
    summary = await nvd_tool.get_severity_summary('CVE-9999-99999')
    
    assert 'error' in summary
    assert summary['error'] == 'CVE not found'


@pytest.mark.asyncio
async def test_enrich_kevs(nvd_tool):
    """Test enriching KEVS data with NVD details"""
    # Sample KEVS data
    kevs_list = [
        {
            'cveID': 'CVE-2021-44228',
            'vendorProject': 'Apache',
            'product': 'Log4j',
            'dateAdded': '2021-12-10'
        }
    ]
    
    enriched = await nvd_tool.enrich_kevs(kevs_list)
    
    assert len(enriched) == 1
    assert 'nvd_data' in enriched[0]
    
    nvd_data = enriched[0]['nvd_data']
    assert 'cvss_scores' in nvd_data
    assert 'cwe' in nvd_data
    assert 'references' in nvd_data
    assert 'description' in nvd_data


@pytest.mark.asyncio
async def test_rate_limiting(nvd_tool):
    """Test that rate limiting is enforced"""
    import time
    
    # Make two requests in quick succession
    start_time = time.time()
    
    await nvd_tool.get_cve('CVE-2021-44228')
    await nvd_tool.get_cve('CVE-2021-44228')  # Will use cache, so won't hit rate limit
    
    # Force non-cached requests
    await nvd_tool.get_cve('CVE-2021-44228', use_cache=False)
    await nvd_tool.get_cve('CVE-2020-1472', use_cache=False)
    
    elapsed = time.time() - start_time
    
    # With rate limiting, should take at least minimum interval
    min_time = 1.0 / nvd_tool.rate_limit
    # Account for two non-cached requests
    assert elapsed >= min_time * 0.5  # Allow some tolerance


def test_api_key_loading():
    """Test that API key is loaded from environment"""
    tool = NVDTool()
    
    # Should either have API key from env or be None
    api_key = os.getenv('NVD_API_KEY')
    assert tool.api_key == api_key


def test_rate_limit_with_api_key():
    """Test that rate limit is correct based on API key presence"""
    tool = NVDTool()
    
    if tool.api_key:
        assert tool.rate_limit == 5  # With API key
    else:
        assert tool.rate_limit == 0.6  # Without API key


def test_base_url_constant():
    """Test that the NVD URL is correctly set"""
    assert NVDTool.BASE_URL == "https://services.nvd.nist.gov/rest/json/cves/2.0"


def test_cache_ttl_default():
    """Test that cache TTL is set to 1 hour by default"""
    tool = NVDTool()
    assert tool.cache_ttl == 3600  # 1 hour in seconds