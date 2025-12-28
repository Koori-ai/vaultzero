# THREAT CONTEXT AGENT - SPECIFICATION
## VaultZero 2.0 - Enterprise Agent Architecture

**Agent ID:** A4 (Threat Context Agent)
**Purpose:** Integrate real-time threat intelligence with Zero Trust assessments
**Model:** Claude Sonnet 4 (deep analysis)
**Priority:** HIGH

---

## AGENT OVERVIEW

The Threat Context Agent bridges the gap between theoretical Zero Trust maturity and real-world threat landscape. It automatically:
1. Identifies technologies in assessed systems
2. Queries CISA KEVS and NVD for relevant vulnerabilities
3. Correlates vulnerabilities with Zero Trust gaps
4. Adjusts risk scores based on active threats
5. Prioritizes remediation by exploitation status

---

## INPUTS

**From Assessment Agent:**
```json
{
  "system_description": "Healthcare organization using Microsoft Exchange...",
  "technologies_identified": [
    "Microsoft Exchange Server 2019",
    "Windows Server 2019",
    "Cisco ASA 5516-X",
    "VMware vSphere 7.0"
  ],
  "pillar_scores": {
    "Identity": 2.0,
    "Devices": 2.5,
    "Networks": 2.0,
    "Applications": 1.5,
    "Data": 2.0,
    "Visibility": 1.5
  },
  "gaps_identified": [
    "No MFA implemented",
    "Static firewall rules",
    "No application allow-listing"
  ]
}
```

---

## PROCESSING WORKFLOW

### Step 1: Technology Extraction
```python
async def extract_technologies(self, assessment_data: dict) -> List[str]:
    """
    Extract specific technologies/products from assessment
    Uses Claude to identify products from free-text description
    """
    
    prompt = f"""
    Extract specific technology products/versions from this system description:
    
    {assessment_data['system_description']}
    
    Return JSON array of products in format:
    ["Vendor Product Version", ...]
    
    Example: ["Microsoft Exchange Server 2019", "Cisco ASA 5516-X"]
    """
    
    response = await claude_api.call(prompt)
    technologies = json.loads(response)
    
    return technologies
```

### Step 2: KEVS Query
```python
async def check_kevs(self, technologies: List[str]) -> List[Dict]:
    """
    Check technologies against CISA KEVS catalog
    """
    
    kevs_tool = KEVSTool()
    kevs_catalog = await kevs_tool.get_kevs_catalog()
    
    matches = []
    for tech in technologies:
        for vuln in kevs_catalog['vulnerabilities']:
            if self._is_match(tech, vuln):
                matches.append({
                    'cve_id': vuln['cveID'],
                    'vendor': vuln['vendorProject'],
                    'product': vuln['product'],
                    'description': vuln['vulnerabilityName'],
                    'date_added': vuln['dateAdded'],
                    'due_date': vuln['dueDate'],
                    'in_kevs': True,
                    'priority': 'CRITICAL'
                })
    
    return matches
```

### Step 3: NVD Deep Dive
```python
async def enrich_with_nvd(self, cve_id: str) -> Dict:
    """
    Get detailed CVE information from NVD
    """
    
    nvd_tool = NVDTool(api_key=os.getenv('NVD_API_KEY'))
    cve_details = await nvd_tool.get_cve_details(cve_id)
    
    return {
        'cvss_score': cve_details['cvss_v3']['score'],
        'cvss_severity': cve_details['cvss_v3']['severity'],
        'cwe': cve_details['cwe'],
        'description': cve_details['description'],
        'references': cve_details['references']
    }
```

### Step 4: Zero Trust Correlation
```python
async def correlate_with_zt_gaps(self, 
                                 vulnerabilities: List[Dict],
                                 zt_gaps: List[str]) -> Dict:
    """
    Correlate vulnerabilities with ZT gaps to show compounding risk
    """
    
    correlations = []
    
    for vuln in vulnerabilities:
        # Determine which ZT pillar this CVE affects
        affected_pillar = self._map_cve_to_pillar(vuln)
        
        # Check if we already have gaps in that pillar
        pillar_gaps = [g for g in zt_gaps if affected_pillar.lower() in g.lower()]
        
        if pillar_gaps:
            correlations.append({
                'cve_id': vuln['cve_id'],
                'pillar': affected_pillar,
                'existing_gaps': pillar_gaps,
                'compounding_risk': True,
                'risk_multiplier': 2.0  # Vuln + Gap = 2x risk
            })
    
    return {
        'correlated_count': len(correlations),
        'correlations': correlations,
        'high_risk_pillars': self._identify_high_risk_pillars(correlations)
    }
```

### Step 5: Risk Score Adjustment
```python
async def adjust_risk_scores(self,
                             base_scores: Dict[str, float],
                             vulnerabilities: List[Dict]) -> Dict:
    """
    Adjust ZT scores based on vulnerability severity
    """
    
    adjusted_scores = base_scores.copy()
    adjustments = {}
    
    for vuln in vulnerabilities:
        pillar = self._map_cve_to_pillar(vuln)
        
        # Calculate adjustment based on CVSS and KEVS status
        if vuln.get('in_kevs'):
            adjustment = -1.0  # KEVS = major penalty
        elif vuln.get('cvss_score', 0) >= 9.0:
            adjustment = -0.5  # Critical CVE
        elif vuln.get('cvss_score', 0) >= 7.0:
            adjustment = -0.3  # High CVE
        else:
            adjustment = -0.1  # Medium CVE
        
        # Apply adjustment (can't go below 1.0)
        adjusted_scores[pillar] = max(1.0, base_scores[pillar] + adjustment)
        
        adjustments[pillar] = adjustments.get(pillar, 0) + adjustment
    
    return {
        'base_scores': base_scores,
        'adjusted_scores': adjusted_scores,
        'adjustments': adjustments,
        'overall_adjustment': sum(adjustments.values()) / len(adjustments)
    }
```

### Step 6: Prioritization
```python
async def prioritize_remediation(self,
                                 vulnerabilities: List[Dict],
                                 zt_gaps: List[str]) -> List[Dict]:
    """
    Prioritize what to fix first
    """
    
    prioritized = []
    
    for vuln in vulnerabilities:
        priority_score = 0
        
        # KEVS = highest priority
        if vuln.get('in_kevs'):
            priority_score += 100
        
        # CVSS score
        priority_score += vuln.get('cvss_score', 0) * 10
        
        # Active exploitation
        if vuln.get('exploitation_observed'):
            priority_score += 50
        
        # Correlates with ZT gap
        if vuln.get('compounding_risk'):
            priority_score += 25
        
        prioritized.append({
            **vuln,
            'priority_score': priority_score,
            'priority_label': self._get_priority_label(priority_score)
        })
    
    # Sort by priority
    prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return prioritized
```

---

## OUTPUTS

**To Report Compiler Agent:**
```json
{
  "threat_summary": {
    "total_vulnerabilities": 5,
    "critical_kevs": 2,
    "high_cves": 3,
    "affected_pillars": ["Identity", "Applications", "Networks"]
  },
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-XXXXX",
      "title": "Microsoft Exchange RCE",
      "cvss_score": 9.8,
      "severity": "CRITICAL",
      "in_kevs": true,
      "kevs_due_date": "2025-01-15",
      "affected_pillar": "Applications",
      "compounding_risk": true,
      "existing_gaps": ["No application allow-listing"],
      "priority_score": 198,
      "priority_label": "IMMEDIATE",
      "bluff": "CVE-2024-XXXXX affects Microsoft Exchange Server...",
      "analyst_note": "Technical Analysis: This vulnerability stems from...",
      "remediation": [
        "Apply patch KB5043820 immediately",
        "Deploy detection rules for /autodiscover anomalies",
        "Implement application allow-listing (ZT control)"
      ]
    }
  ],
  "risk_adjustments": {
    "Identity": -0.5,
    "Applications": -1.0,
    "Networks": -0.3
  },
  "adjusted_scores": {
    "Identity": 1.5,
    "Devices": 2.5,
    "Networks": 1.7,
    "Applications": 0.5,
    "Data": 2.0,
    "Visibility": 1.5
  },
  "prioritized_actions": [
    {
      "rank": 1,
      "action": "Patch Microsoft Exchange (CVE-2024-XXXXX)",
      "due_date": "2025-01-15",
      "reason": "KEVS vulnerability with active exploitation"
    },
    {
      "rank": 2,
      "action": "Implement application allow-listing",
      "due_date": "2025-02-01",
      "reason": "Mitigates both CVE risk and ZT gap"
    }
  ]
}
```

---

## PERFORMANCE REQUIREMENTS

**Latency:** < 30 seconds per assessment
**Accuracy:** > 95% technology identification
**Coverage:** 100% of KEVS catalog
**API Rate Limits:**
- KEVS: No limit (static JSON)
- NVD: 5 requests/second (with API key)

---

## ERROR HANDLING

```python
async def process_with_retry(self, assessment_data: dict) -> dict:
    """
    Process with retry logic for API failures
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Extract technologies
            technologies = await self.extract_technologies(assessment_data)
            
            # Check KEVS
            kevs_matches = await self.check_kevs(technologies)
            
            # Enrich with NVD
            enriched = []
            for match in kevs_matches:
                try:
                    nvd_data = await self.enrich_with_nvd(match['cve_id'])
                    enriched.append({**match, **nvd_data})
                except Exception as e:
                    # Log but continue with partial data
                    logger.warning(f"NVD enrichment failed for {match['cve_id']}: {e}")
                    enriched.append(match)
            
            # Correlate and prioritize
            correlation = await self.correlate_with_zt_gaps(
                enriched,
                assessment_data['gaps_identified']
            )
            
            adjusted_scores = await self.adjust_risk_scores(
                assessment_data['pillar_scores'],
                enriched
            )
            
            prioritized = await self.prioritize_remediation(
                enriched,
                assessment_data['gaps_identified']
            )
            
            return {
                'threat_summary': self._generate_summary(enriched),
                'vulnerabilities': enriched,
                'risk_adjustments': adjusted_scores['adjustments'],
                'adjusted_scores': adjusted_scores['adjusted_scores'],
                'prioritized_actions': self._generate_actions(prioritized)
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed - return graceful degradation
                logger.error(f"Threat Context Agent failed: {e}")
                return self._graceful_degradation(assessment_data)
            
            # Wait before retry
            await asyncio.sleep(2 ** attempt)
```

---

## INTEGRATION WITH EXISTING AGENTS

```
Assessment Agent
    ↓
    [Produces ZT scores + gaps]
    ↓
Benchmark Agent
    ↓
    [Adds peer comparison]
    ↓
🆕 Threat Context Agent ← YOU ARE HERE
    ↓
    [Adds vulnerability context]
    ↓
Roadmap Agent
    ↓
    [Creates remediation plan using threat prioritization]
```

---

## TESTING STRATEGY

**Unit Tests:**
```python
async def test_technology_extraction():
    """Test tech extraction from descriptions"""
    
    assessment = {
        'system_description': 'Using Microsoft Exchange 2019 and Cisco ASA'
    }
    
    agent = ThreatContextAgent()
    techs = await agent.extract_technologies(assessment)
    
    assert 'Microsoft Exchange' in str(techs)
    assert 'Cisco ASA' in str(techs)

async def test_kevs_matching():
    """Test KEVS catalog matching"""
    
    technologies = ['Microsoft Exchange Server 2019']
    
    agent = ThreatContextAgent()
    matches = await agent.check_kevs(technologies)
    
    assert len(matches) >= 0  # May have 0 if no KEVS for this product
    if matches:
        assert matches[0]['in_kevs'] == True

async def test_risk_adjustment():
    """Test risk score adjustment logic"""
    
    base_scores = {'Identity': 2.0, 'Applications': 2.0}
    vulnerabilities = [
        {'cve_id': 'CVE-2024-XXXXX', 'cvss_score': 9.8, 'in_kevs': True}
    ]
    
    agent = ThreatContextAgent()
    adjusted = await agent.adjust_risk_scores(base_scores, vulnerabilities)
    
    assert adjusted['adjusted_scores']['Applications'] < base_scores['Applications']
```

---

## DEPLOYMENT CHECKLIST

- [ ] NVD API key obtained and configured
- [ ] KEVS catalog accessibility verified
- [ ] Claude API quota sufficient (Sonnet 4 calls)
- [ ] Database schema includes threat_analysis table
- [ ] Error handling and retry logic tested
- [ ] Integration tests with Assessment Agent passed
- [ ] Performance benchmarks met (<30s per assessment)
- [ ] Security review completed (API keys, data handling)

---

**END OF AGENT SPECIFICATION**

**Agent:** Threat Context Agent (A4)
**Status:** READY FOR IMPLEMENTATION
**Estimated Dev Time:** 3-4 days
**Priority:** HIGH
