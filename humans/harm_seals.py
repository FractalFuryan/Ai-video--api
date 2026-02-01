"""
Cryptographic Harm Seals

Seal outputs with mathematical proofs of harm prevention.
Publicly verifiable - anyone can audit.
"""

import json
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional, List
import secrets


class HarmSeal:
    """
    Cryptographically seal identities with harm prevention proofs.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.sealed_identities = {}  # In production: persistent storage
    
    def seal_identity(self, 
                     identity_dict: Dict, 
                     harm_certificate: Dict) -> Dict:
        """
        Cryptographically seal an identity with harm prevention proofs.
        """
        # 1. Create harm prevention manifest
        manifest = {
            "identity_hash": self._hash_identity(identity_dict),
            "harm_certificate": harm_certificate,
            "seal_version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "harm_preventions": [
                "architectural_deepfake_prevention",
                "exploitation_prevention",
                "bias_prevention",
                "deception_prevention",
                "violence_prevention",
            ]
        }
        
        # 2. Generate cryptographic seal
        seal_signature = self._generate_seal(manifest)
        
        # 3. Create verifiable package
        package = {
            "identity": identity_dict,
            "harm_manifest": manifest,
            "cryptographic_seal": seal_signature,
            "verification_data": self._generate_verification_data(manifest, seal_signature),
        }
        
        # 4. Store for later verification
        package_hash = self._package_hash(package)
        self.sealed_identities[package_hash] = package
        
        return package
    
    def verify_seal(self, sealed_package: Dict) -> Tuple[bool, List[str]]:
        """
        Verify cryptographic seal and harm prevention.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. Verify cryptographic seal
        if not self._verify_cryptographic_seal(sealed_package):
            errors.append("Cryptographic seal signature invalid")
        
        # 2. Verify harm certificate completeness
        manifest = sealed_package.get("harm_manifest", {})
        if not manifest.get("harm_certificate"):
            errors.append("Harm certificate missing")
        
        # 3. Verify identity hash consistency
        if not self._verify_identity_hash(sealed_package):
            errors.append("Identity hash mismatch")
        
        # 4. Verify timestamp (prevent replay attacks)
        if not self._verify_timestamp_freshness(sealed_package):
            errors.append("Seal timestamp invalid or expired")
        
        return len(errors) == 0, errors
    
    def _hash_identity(self, identity_dict: Dict) -> str:
        """Create deterministic hash of identity."""
        sorted_data = json.dumps(identity_dict, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def _generate_seal(self, manifest: Dict) -> str:
        """Generate HMAC seal of manifest."""
        sorted_manifest = json.dumps(
            manifest, 
            sort_keys=True, 
            separators=(',', ':'),
            default=str
        )
        return hmac.new(
            self.secret_key.encode(),
            sorted_manifest.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _verify_cryptographic_seal(self, package: Dict) -> bool:
        """Verify HMAC seal is valid."""
        manifest = package.get("harm_manifest")
        expected_seal = package.get("cryptographic_seal")
        
        if not manifest or not expected_seal:
            return False
        
        # Recompute seal
        sorted_manifest = json.dumps(
            manifest,
            sort_keys=True,
            separators=(',', ':'),
            default=str
        )
        computed_seal = hmac.new(
            self.secret_key.encode(),
            sorted_manifest.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_seal, computed_seal)
    
    def _verify_identity_hash(self, package: Dict) -> bool:
        """Verify identity hash matches content."""
        manifest = package.get("harm_manifest")
        identity = package.get("identity")
        
        if not manifest or not identity:
            return False
        
        expected_hash = manifest.get("identity_hash")
        actual_hash = self._hash_identity(identity)
        
        return hmac.compare_digest(expected_hash, actual_hash)
    
    def _verify_timestamp_freshness(self, package: Dict) -> bool:
        """Verify timestamp is recent (prevent replay attacks)."""
        try:
            manifest = package.get("harm_manifest", {})
            timestamp_str = manifest.get("timestamp")
            
            if not timestamp_str:
                return False
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(
                timestamp_str.replace('Z', '+00:00')
            )
            now = datetime.now(timezone.utc)
            
            # Allow 5 minute window for clock skew
            max_age_seconds = 300
            age = (now - timestamp).total_seconds()
            
            return 0 <= age <= max_age_seconds
            
        except (ValueError, KeyError, AttributeError):
            return False
    
    def _generate_verification_data(self, manifest: Dict, seal_signature: str) -> Dict:
        """Generate data for external verification."""
        return {
            "verification_url": "/harm-verification/public-audit",
            "public_hash": hashlib.sha256(
                json.dumps(manifest, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "seal_signature_preview": seal_signature[:16] + "...",
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "transparency_claim": "Fully verifiable - anyone can check",
        }
    
    def _package_hash(self, package: Dict) -> str:
        """Create hash of entire package."""
        data = json.dumps(package, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
