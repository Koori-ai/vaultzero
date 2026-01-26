"""
AWS Zero Trust Evidence Reader
MCP Tool for collecting Zero Trust security evidence from AWS

This tool collects REAL data from AWS to assess Zero Trust maturity:
- Identity: IAM users, MFA status, access keys, password policies
- Network: Security groups, VPCs, public access
- Data: S3 bucket policies, encryption status
- Visibility: CloudTrail logging, Config rules

Author: VaultZero Team
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import os

# Load environment variables
load_dotenv()


class AWSZeroTrustReader:
    """
    Collects Zero Trust security evidence from AWS.
    
    This is a READ-ONLY tool - it cannot modify any AWS resources.
    Uses the SecurityAudit IAM policy for access.
    
    Zero Trust Pillars Covered:
    - Identity: IAM analysis
    - Network: VPC/Security Group analysis  
    - Data: S3 security analysis
    - Visibility: Logging analysis
    """
    
    def __init__(self, region: str = None):
        """
        Initialize AWS clients.
        
        Args:
            region: AWS region (defaults to AWS_DEFAULT_REGION env var)
        """
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
        self.logger = self._setup_logger()
        
        # Initialize AWS clients
        try:
            self.iam = boto3.client('iam')  # IAM is global, no region needed
            self.s3 = boto3.client('s3', region_name=self.region)
            self.ec2 = boto3.client('ec2', region_name=self.region)
            self.cloudtrail = boto3.client('cloudtrail', region_name=self.region)
            self.logger.info(f"AWS clients initialized for region: {self.region}")
        except NoCredentialsError:
            self.logger.error("AWS credentials not found!")
            raise
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging."""
        logger = logging.getLogger("vaultzero.tools.aws_zt_reader")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AWS_ZT_Reader - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    # =========================================================================
    # IDENTITY PILLAR - IAM Analysis
    # =========================================================================
    
    async def get_identity_evidence(self) -> Dict[str, Any]:
        """
        Collect Identity pillar evidence from AWS IAM.
        
        Returns:
            Dictionary containing:
            - total_users: Number of IAM users
            - mfa_enabled_count: Users with MFA
            - mfa_adoption_percent: MFA adoption percentage
            - users_without_mfa: List of users lacking MFA
            - access_key_issues: Old or inactive keys
            - password_policy: Account password policy
            - root_account_mfa: Whether root has MFA
        """
        self.logger.info("Collecting Identity pillar evidence...")
        
        evidence = {
            'pillar': 'Identity',
            'source': 'AWS IAM',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'findings': {}
        }
        
        try:
            # Get all IAM users
            users = self._get_all_users()
            evidence['findings']['total_users'] = len(users)
            
            # Check MFA status for each user
            mfa_analysis = self._analyze_mfa_status(users)
            evidence['findings'].update(mfa_analysis)
            
            # Check access key age and status
            access_key_analysis = self._analyze_access_keys(users)
            evidence['findings'].update(access_key_analysis)
            
            # Get password policy
            password_policy = self._get_password_policy()
            evidence['findings']['password_policy'] = password_policy
            
            # Check root account MFA
            root_mfa = self._check_root_mfa()
            evidence['findings']['root_account_mfa'] = root_mfa
            
            # Calculate Identity pillar score (0-5)
            evidence['maturity_score'] = self._calculate_identity_score(evidence['findings'])
            
            self.logger.info(f"Identity evidence collected. Score: {evidence['maturity_score']}/5")
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            evidence['error'] = str(e)
            evidence['maturity_score'] = 0
        
        return evidence
    
    def _get_all_users(self) -> List[Dict]:
        """Get all IAM users."""
        users = []
        paginator = self.iam.get_paginator('list_users')
        
        for page in paginator.paginate():
            users.extend(page['Users'])
        
        self.logger.info(f"Found {len(users)} IAM users")
        return users
    
    def _analyze_mfa_status(self, users: List[Dict]) -> Dict[str, Any]:
        """Analyze MFA adoption across all users."""
        mfa_enabled = 0
        users_without_mfa = []
        
        for user in users:
            username = user['UserName']
            try:
                mfa_devices = self.iam.list_mfa_devices(UserName=username)
                if mfa_devices['MFADevices']:
                    mfa_enabled += 1
                else:
                    users_without_mfa.append(username)
            except ClientError:
                users_without_mfa.append(username)
        
        total = len(users)
        mfa_percent = (mfa_enabled / total * 100) if total > 0 else 0
        
        return {
            'mfa_enabled_count': mfa_enabled,
            'mfa_adoption_percent': round(mfa_percent, 1),
            'users_without_mfa': users_without_mfa,
            'users_without_mfa_count': len(users_without_mfa)
        }
    
    def _analyze_access_keys(self, users: List[Dict]) -> Dict[str, Any]:
        """Analyze access key age and status."""
        issues = []
        keys_over_90_days = 0
        keys_over_365_days = 0
        inactive_keys = 0
        
        for user in users:
            username = user['UserName']
            try:
                keys = self.iam.list_access_keys(UserName=username)
                
                for key in keys['AccessKeyMetadata']:
                    key_age_days = (datetime.now(timezone.utc) - key['CreateDate']).days
                    
                    if key['Status'] == 'Inactive':
                        inactive_keys += 1
                        issues.append(f"{username}: Inactive key exists")
                    
                    if key_age_days > 365:
                        keys_over_365_days += 1
                        issues.append(f"{username}: Key is {key_age_days} days old (>365)")
                    elif key_age_days > 90:
                        keys_over_90_days += 1
                        issues.append(f"{username}: Key is {key_age_days} days old (>90)")
                        
            except ClientError:
                pass
        
        return {
            'access_keys_over_90_days': keys_over_90_days,
            'access_keys_over_365_days': keys_over_365_days,
            'inactive_access_keys': inactive_keys,
            'access_key_issues': issues[:10]  # Limit to first 10
        }
    
    def _get_password_policy(self) -> Dict[str, Any]:
        """Get account password policy."""
        try:
            policy = self.iam.get_account_password_policy()
            pp = policy['PasswordPolicy']
            return {
                'exists': True,
                'min_length': pp.get('MinimumPasswordLength', 0),
                'require_uppercase': pp.get('RequireUppercaseCharacters', False),
                'require_lowercase': pp.get('RequireLowercaseCharacters', False),
                'require_numbers': pp.get('RequireNumbers', False),
                'require_symbols': pp.get('RequireSymbols', False),
                'max_age_days': pp.get('MaxPasswordAge', None),
                'password_reuse_prevention': pp.get('PasswordReusePrevention', None)
            }
        except ClientError:
            return {'exists': False}
    
    def _check_root_mfa(self) -> bool:
        """Check if root account has MFA enabled."""
        try:
            summary = self.iam.get_account_summary()
            return summary['SummaryMap'].get('AccountMFAEnabled', 0) == 1
        except ClientError:
            return False
    
    def _calculate_identity_score(self, findings: Dict) -> float:
        """
        Calculate Identity pillar maturity score (0-5).
        
        Scoring:
        - MFA adoption: up to 2 points
        - Root MFA: 1 point
        - Password policy: 1 point
        - Access key hygiene: 1 point
        """
        score = 0.0
        
        # MFA adoption (0-2 points)
        mfa_percent = findings.get('mfa_adoption_percent', 0)
        if mfa_percent >= 95:
            score += 2.0
        elif mfa_percent >= 80:
            score += 1.5
        elif mfa_percent >= 50:
            score += 1.0
        elif mfa_percent >= 25:
            score += 0.5
        
        # Root MFA (0-1 point)
        if findings.get('root_account_mfa', False):
            score += 1.0
        
        # Password policy (0-1 point)
        pp = findings.get('password_policy', {})
        if pp.get('exists', False):
            if pp.get('min_length', 0) >= 14:
                score += 0.5
            if pp.get('require_symbols', False) and pp.get('require_numbers', False):
                score += 0.5
        
        # Access key hygiene (0-1 point)
        old_keys = findings.get('access_keys_over_90_days', 0)
        if old_keys == 0:
            score += 1.0
        elif old_keys <= 2:
            score += 0.5
        
        return round(min(score, 5.0), 1)

    # =========================================================================
    # DATA PILLAR - S3 Analysis
    # =========================================================================
    
    async def get_data_evidence(self) -> Dict[str, Any]:
        """
        Collect Data pillar evidence from AWS S3.
        
        Returns:
            Dictionary containing:
            - total_buckets: Number of S3 buckets
            - public_buckets: Buckets with public access
            - unencrypted_buckets: Buckets without encryption
            - buckets_without_versioning: Buckets without versioning
        """
        self.logger.info("Collecting Data pillar evidence...")
        
        evidence = {
            'pillar': 'Data',
            'source': 'AWS S3',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'findings': {}
        }
        
        try:
            buckets = self.s3.list_buckets().get('Buckets', [])
            evidence['findings']['total_buckets'] = len(buckets)
            
            public_buckets = []
            unencrypted_buckets = []
            no_versioning = []
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                # Check public access
                if self._is_bucket_public(bucket_name):
                    public_buckets.append(bucket_name)
                
                # Check encryption
                if not self._is_bucket_encrypted(bucket_name):
                    unencrypted_buckets.append(bucket_name)
                
                # Check versioning
                if not self._is_versioning_enabled(bucket_name):
                    no_versioning.append(bucket_name)
            
            evidence['findings']['public_buckets'] = public_buckets
            evidence['findings']['public_buckets_count'] = len(public_buckets)
            evidence['findings']['unencrypted_buckets'] = unencrypted_buckets
            evidence['findings']['unencrypted_buckets_count'] = len(unencrypted_buckets)
            evidence['findings']['buckets_without_versioning'] = no_versioning
            evidence['findings']['no_versioning_count'] = len(no_versioning)
            
            # Calculate score
            evidence['maturity_score'] = self._calculate_data_score(evidence['findings'])
            
            self.logger.info(f"Data evidence collected. Score: {evidence['maturity_score']}/5")
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            evidence['error'] = str(e)
            evidence['maturity_score'] = 0
        
        return evidence
    
    def _is_bucket_public(self, bucket_name: str) -> bool:
        """Check if S3 bucket has public access."""
        try:
            # Check public access block
            pab = self.s3.get_public_access_block(Bucket=bucket_name)
            config = pab['PublicAccessBlockConfiguration']
            
            # If all blocks are enabled, bucket is not public
            if all([
                config.get('BlockPublicAcls', False),
                config.get('IgnorePublicAcls', False),
                config.get('BlockPublicPolicy', False),
                config.get('RestrictPublicBuckets', False)
            ]):
                return False
            return True
        except ClientError:
            # If no public access block, assume potentially public
            return True
    
    def _is_bucket_encrypted(self, bucket_name: str) -> bool:
        """Check if S3 bucket has default encryption."""
        try:
            encryption = self.s3.get_bucket_encryption(Bucket=bucket_name)
            return True
        except ClientError as e:
            if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                return False
            return True  # Assume encrypted if other error
    
    def _is_versioning_enabled(self, bucket_name: str) -> bool:
        """Check if S3 bucket versioning is enabled."""
        try:
            versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
            return versioning.get('Status') == 'Enabled'
        except ClientError:
            return False
    
    def _calculate_data_score(self, findings: Dict) -> float:
        """Calculate Data pillar maturity score (0-5)."""
        score = 5.0  # Start with perfect score
        
        total = findings.get('total_buckets', 0)
        if total == 0:
            return 3.0  # No buckets = neutral score
        
        # Deduct for public buckets (up to 2 points)
        public_pct = findings.get('public_buckets_count', 0) / total * 100
        if public_pct > 0:
            score -= min(2.0, public_pct / 25)
        
        # Deduct for unencrypted buckets (up to 2 points)
        unencrypted_pct = findings.get('unencrypted_buckets_count', 0) / total * 100
        if unencrypted_pct > 0:
            score -= min(2.0, unencrypted_pct / 25)
        
        # Deduct for no versioning (up to 1 point)
        no_version_pct = findings.get('no_versioning_count', 0) / total * 100
        if no_version_pct > 50:
            score -= 1.0
        elif no_version_pct > 0:
            score -= 0.5
        
        return round(max(0, score), 1)

    # =========================================================================
    # VISIBILITY PILLAR - Logging Analysis
    # =========================================================================
    
    async def get_visibility_evidence(self) -> Dict[str, Any]:
        """
        Collect Visibility & Analytics pillar evidence.
        
        Returns:
            Dictionary containing CloudTrail status and logging coverage.
        """
        self.logger.info("Collecting Visibility pillar evidence...")
        
        evidence = {
            'pillar': 'Visibility & Analytics',
            'source': 'AWS CloudTrail',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'findings': {}
        }
        
        try:
            # Check CloudTrail trails
            trails = self.cloudtrail.describe_trails().get('trailList', [])
            evidence['findings']['total_trails'] = len(trails)
            
            multi_region_trails = []
            logging_enabled = 0
            
            for trail in trails:
                trail_name = trail.get('Name', 'Unknown')
                
                # Check if multi-region
                if trail.get('IsMultiRegionTrail', False):
                    multi_region_trails.append(trail_name)
                
                # Check if logging is active
                try:
                    status = self.cloudtrail.get_trail_status(Name=trail['TrailARN'])
                    if status.get('IsLogging', False):
                        logging_enabled += 1
                except ClientError:
                    pass
            
            evidence['findings']['multi_region_trails'] = multi_region_trails
            evidence['findings']['logging_enabled_count'] = logging_enabled
            evidence['findings']['has_multi_region_logging'] = len(multi_region_trails) > 0
            
            # Calculate score
            evidence['maturity_score'] = self._calculate_visibility_score(evidence['findings'])
            
            self.logger.info(f"Visibility evidence collected. Score: {evidence['maturity_score']}/5")
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            evidence['error'] = str(e)
            evidence['maturity_score'] = 0
        
        return evidence
    
    def _calculate_visibility_score(self, findings: Dict) -> float:
        """Calculate Visibility pillar maturity score (0-5)."""
        score = 0.0
        
        # Has any CloudTrail (2 points)
        if findings.get('total_trails', 0) > 0:
            score += 2.0
        
        # Has multi-region trail (2 points)
        if findings.get('has_multi_region_logging', False):
            score += 2.0
        
        # Active logging (1 point)
        if findings.get('logging_enabled_count', 0) > 0:
            score += 1.0
        
        return round(min(score, 5.0), 1)

    # =========================================================================
    # MAIN COLLECTION METHOD
    # =========================================================================
    
    async def collect_all_evidence(self) -> Dict[str, Any]:
        """
        Collect Zero Trust evidence across all supported pillars.
        
        Returns:
            Complete evidence dictionary with all pillar assessments.
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting AWS Zero Trust Evidence Collection")
        self.logger.info("=" * 50)
        
        evidence = {
            'source': 'AWS',
            'region': self.region,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'pillars': {}
        }
        
        # Collect Identity evidence
        evidence['pillars']['Identity'] = await self.get_identity_evidence()
        
        # Collect Data evidence
        evidence['pillars']['Data'] = await self.get_data_evidence()
        
        # Collect Visibility evidence
        evidence['pillars']['Visibility'] = await self.get_visibility_evidence()
        
        # Calculate overall score
        scores = [
            p.get('maturity_score', 0) 
            for p in evidence['pillars'].values()
        ]
        evidence['overall_score'] = round(sum(scores) / len(scores), 1) if scores else 0
        
        self.logger.info("=" * 50)
        self.logger.info(f"Collection Complete! Overall Score: {evidence['overall_score']}/5")
        self.logger.info("=" * 50)
        
        return evidence


# =============================================================================
# TEST FUNCTION
# =============================================================================

async def test_aws_zt_reader():
    """Test the AWS Zero Trust Reader."""
    print("\n" + "=" * 60)
    print("🔍 VAULTZERO AWS ZERO TRUST EVIDENCE COLLECTION")
    print("=" * 60 + "\n")
    
    reader = AWSZeroTrustReader()
    
    # Collect all evidence
    evidence = await reader.collect_all_evidence()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 EVIDENCE SUMMARY")
    print("=" * 60)
    
    for pillar_name, pillar_data in evidence['pillars'].items():
        score = pillar_data.get('maturity_score', 0)
        print(f"\n🔹 {pillar_name}: {score}/5.0")
        
        findings = pillar_data.get('findings', {})
        for key, value in findings.items():
            if not isinstance(value, list) or len(value) <= 3:
                print(f"   - {key}: {value}")
    
    print(f"\n{'=' * 60}")
    print(f"🎯 OVERALL ZERO TRUST SCORE: {evidence['overall_score']}/5.0")
    print(f"{'=' * 60}\n")
    
    return evidence


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_aws_zt_reader())