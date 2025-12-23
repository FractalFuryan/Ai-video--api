"""
HarmonyØ4 Compression Engine Attestation — Runtime Proof

Provides cryptographic attestation that a specific compression core is active.
This enables runtime verification of which engine produced a particular container.

SAFETY:
- No secrets disclosed
- No algorithm exposed
- Pure structural information
- Immutable (once computed)
- Auditable
"""

import hashlib
import time
from typing import Dict, Any


def attest() -> Dict[str, Any]:
    """
    Generate runtime attestation of active compression engine.
    
    Returns a dict proving:
    1. Which engine is loaded (engine_id)
    2. Its identity fingerprint (SHA256 of core)
    3. Current timestamp (freshness)
    4. Attestation hash (proof of this exact state)
    
    Safe to publish:
    - No algorithm details
    - No internal constants
    - No security parameters
    
    Returns:
        Attestation dict with engine, fingerprint, timestamp, proof
        
    Example:
        >>> attest()
        {
            'engine_id': 'h4core-geo-v1.2.3',
            'fingerprint': 'a7c4b1d9e2f0a3c5...',
            'timestamp_unix': 1703349600,
            'attestation_hash': 'e91d5c8b4a2f...',
            'sealed': True
        }
    """
    # Avoid circular import by importing late
    from compression import get_engine
    
    engine_info = get_engine().info()
    
    timestamp_unix = int(time.time())
    
    # Attestation message: engine_id | fingerprint | timestamp
    msg = f"{engine_info.get('engine_id', 'unknown')}|{engine_info.get('fingerprint', 'unknown')}|{timestamp_unix}"
    attestation_hash = hashlib.sha256(msg.encode()).hexdigest()
    
    return {
        "engine_id": engine_info.get("engine_id", "unknown"),
        "fingerprint": engine_info.get("fingerprint", "unknown"),
        "timestamp_unix": timestamp_unix,
        "attestation_hash": attestation_hash,
        "sealed": bool(engine_info.get("sealed", False)),
        "engine": engine_info.get("engine", "unknown"),
    }


def verify_attestation(attestation: Dict[str, Any]) -> bool:
    """
    Verify that an attestation matches current engine state.
    
    Args:
        attestation: Dict from attest() call
        
    Returns:
        True if engine_id and fingerprint match current state
        
    Raises:
        ValueError: If attestation format invalid
    """
    required_fields = ["engine_id", "fingerprint", "timestamp_unix", "attestation_hash"]
    if not all(k in attestation for k in required_fields):
        raise ValueError(f"Attestation missing required fields: {required_fields}")
    
    current = attest()
    
    # Match engine_id and fingerprint
    return (
        attestation["engine_id"] == current["engine_id"] and
        attestation["fingerprint"] == current["fingerprint"]
    )
