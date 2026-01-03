"""
VaultZero Threat Intel Dashboard
Standalone dashboard for viewing and analyzing CISA KEVS with NVD enrichment
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from tools.kevs_tool import KEVSTool
from tools.nvd_tool import NVDTool


# Page configuration
st.set_page_config(
    page_title="VaultZero Threat Intel Dashboard",
    page_icon="🔒",
    layout="wide"
)


async def load_kevs_data(days=7):
    """Load KEVS data for the specified number of days"""
    kevs_tool = KEVSTool()
    nvd_tool = NVDTool()
    
    # Get KEVS from specified time period
    if days == 1:
        kevs = await kevs_tool.get_daily_kevs()
    elif days == 7:
        kevs = await kevs_tool.get_weekly_kevs()
    else:
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        kevs = await kevs_tool.get_new_kevs(since_date)
    
    # Get catalog stats
    stats = await kevs_tool.get_catalog_stats()
    
    # Enrich with NVD data (limit to prevent slow loading)
    if kevs and len(kevs) <= 20:
        with st.spinner('Enriching with NVD CVE details...'):
            enriched = await nvd_tool.enrich_kevs(kevs)
    else:
        enriched = kevs
    
    return enriched, stats


def extract_severity(vuln):
    """Extract severity from enriched vulnerability data"""
    if 'nvd_data' in vuln:
        scores = vuln['nvd_data'].get('cvss_scores', {})
        if scores.get('cvss_v31'):
            return scores['cvss_v31'].get('baseSeverity', 'UNKNOWN')
        elif scores.get('cvss_v30'):
            return scores['cvss_v30'].get('baseSeverity', 'UNKNOWN')
    return 'UNKNOWN'


def extract_score(vuln):
    """Extract CVSS score from enriched vulnerability data"""
    if 'nvd_data' in vuln:
        scores = vuln['nvd_data'].get('cvss_scores', {})
        if scores.get('cvss_v31'):
            return scores['cvss_v31'].get('baseScore', 0)
        elif scores.get('cvss_v30'):
            return scores['cvss_v30'].get('baseScore', 0)
        elif scores.get('cvss_v2'):
            return scores['cvss_v2'].get('baseScore', 0)
    return 0


def severity_color(severity):
    """Return color for severity level"""
    colors = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢',
        'UNKNOWN': '⚪'
    }
    return colors.get(severity, '⚪')


def main():
    # Header
    st.title("🔒 VaultZero Threat Intel Dashboard")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown("**TLP: GREEN**")
    with col2:
        st.markdown(f"**Generated:** {datetime.now().strftime('%B %d, %Y %H:%M EST')}")
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.divider()
    
    # Sidebar filters
    st.sidebar.header("⚙️ Filter Options")
    
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=[1, 7, 14, 30, 90],
        index=1,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
    )
    
    vendor_filter = st.sidebar.text_input("Filter by Vendor", "")
    product_filter = st.sidebar.text_input("Filter by Product", "")
    
    severity_filter = st.sidebar.multiselect(
        "Filter by Severity",
        options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'],
        default=[]
    )
    
    # Load data
    with st.spinner('Loading KEVS catalog...'):
        kevs, stats = asyncio.run(load_kevs_data(days=time_range))
    
    # Summary Statistics
    st.header("📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total KEVS in Catalog", f"{stats['total_kevs']:,}")
    
    with col2:
        st.metric(f"New in Last {time_range} Days", len(kevs))
    
    with col3:
        critical_count = sum(1 for v in kevs if extract_severity(v) == 'CRITICAL')
        st.metric("Critical Severity", critical_count)
    
    with col4:
        high_count = sum(1 for v in kevs if extract_severity(v) == 'HIGH')
        st.metric("High Severity", high_count)
    
    st.markdown(f"**Catalog Version:** {stats['catalog_version']} | **Released:** {stats['date_released']}")
    
    st.divider()
    
    # Apply filters
    filtered_kevs = kevs.copy()
    
    if vendor_filter:
        filtered_kevs = [v for v in filtered_kevs 
                        if vendor_filter.lower() in v.get('vendorProject', '').lower()]
    
    if product_filter:
        filtered_kevs = [v for v in filtered_kevs 
                        if product_filter.lower() in v.get('product', '').lower()]
    
    if severity_filter:
        filtered_kevs = [v for v in filtered_kevs 
                        if extract_severity(v) in severity_filter]
    
    # Severity Distribution Chart
    if filtered_kevs:
        st.header("📈 Severity Distribution")
        
        severity_counts = {}
        for vuln in filtered_kevs:
            sev = extract_severity(vuln)
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        # Create DataFrame for chart
        df_severity = pd.DataFrame([
            {'Severity': k, 'Count': v} 
            for k, v in severity_counts.items()
        ])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.bar_chart(df_severity.set_index('Severity'))
        
        with col2:
            st.dataframe(
                df_severity.sort_values('Count', ascending=False),
                hide_index=True,
                use_container_width=True
            )
    
    st.divider()
    
    # KEVS Table
    st.header(f"📋 KEVS List ({len(filtered_kevs)} vulnerabilities)")
    
    if not filtered_kevs:
        st.info("No vulnerabilities found matching your filters.")
    else:
        # Display each vulnerability
        for idx, vuln in enumerate(filtered_kevs):
            severity = extract_severity(vuln)
            score = extract_score(vuln)
            
            with st.expander(
                f"{severity_color(severity)} **{vuln['cveID']}** - {vuln['vendorProject']} {vuln['product']} "
                f"({severity}: {score if score > 0 else 'N/A'})"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Vendor/Project:** {vuln['vendorProject']}")
                    st.markdown(f"**Product:** {vuln['product']}")
                    st.markdown(f"**Vulnerability:** {vuln['vulnerabilityName']}")
                    st.markdown(f"**Added to KEVS:** {vuln['dateAdded']}")
                    st.markdown(f"**Due Date:** {vuln['dueDate']}")
                    
                    st.markdown("**KEVS Description:**")
                    st.info(vuln['shortDescription'])
                    
                    st.markdown("**Required Action:**")
                    st.warning(vuln['requiredAction'])
                
                with col2:
                    if 'nvd_data' in vuln:
                        nvd = vuln['nvd_data']
                        
                        st.markdown("### 🔍 NVD Details")
                        
                        # CVSS Score
                        if score > 0:
                            st.metric("CVSS Score", f"{score:.1f}", delta=severity)
                        
                        # CWE
                        if nvd.get('cwe'):
                            st.markdown(f"**CWE:** {', '.join(nvd['cwe'])}")
                        
                        # Dates
                        if nvd.get('published'):
                            pub_date = nvd['published'][:10]
                            st.markdown(f"**Published:** {pub_date}")
                        
                        # Description
                        if nvd.get('description'):
                            st.markdown("**NVD Description:**")
                            st.caption(nvd['description'][:300] + "...")
                        
                        # References count
                        if nvd.get('references'):
                            st.markdown(f"**References:** {len(nvd['references'])} links available")
                    else:
                        st.info("NVD data not loaded for this CVE")
    
    st.divider()
    
    # Export Options
    st.header("📄 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export to CSV"):
            # Convert to DataFrame
            data_rows = []
            for vuln in filtered_kevs:
                row = {
                    'CVE ID': vuln['cveID'],
                    'Vendor': vuln['vendorProject'],
                    'Product': vuln['product'],
                    'Vulnerability': vuln['vulnerabilityName'],
                    'Date Added': vuln['dateAdded'],
                    'Due Date': vuln['dueDate'],
                    'Severity': extract_severity(vuln),
                    'CVSS Score': extract_score(vuln),
                    'Description': vuln['shortDescription'],
                    'Required Action': vuln['requiredAction']
                }
                
                # Add NVD data if available
                if 'nvd_data' in vuln:
                    nvd = vuln['nvd_data']
                    row['CWE'] = ', '.join(nvd.get('cwe', []))
                    row['NVD Description'] = nvd.get('description', '')
                
                data_rows.append(row)
            
            df = pd.DataFrame(data_rows)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"vaultzero_kevs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.info("📝 DOCX export coming in Day 3!")
    
    with col3:
        st.info("📊 PDF export coming in Day 4!")
    
    # Footer
    st.divider()
    st.caption("VaultZero Threat Intel Dashboard | Powered by CISA KEVS & NIST NVD")


if __name__ == "__main__":
    main()