"""
Real-time Harm Monitoring System

Monitor and prevent harmful generation attempts in real-time.
"""

from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class HarmAttemptType(Enum):
    """Types of harmful generation attempts."""
    DEEPFAKE_ATTEMPT = "deepfake_attempt"
    EXPLOITATION_ATTEMPT = "exploitation_attempt"
    BIAS_ATTEMPT = "bias_attempt"
    VIOLENCE_ATTEMPT = "violence_attempt"
    DECEPTION_ATTEMPT = "deception_attempt"


class HarmMonitor:
    """
    Real-time monitoring of generation attempts.
    Prevents harmful content generation in real-time.
    """
    
    def __init__(self, redis_client: Optional[object] = None):
        self.redis = redis_client
        self.blocked_patterns = self._load_blocked_patterns()
        self.harm_attempts = defaultdict(list)
        
        # Harmful prompt patterns
        self.harm_patterns = {
            HarmAttemptType.DEEPFAKE_ATTEMPT: [
                "make me look like", "look like person", "resemble",
                "match to", "generate face of", "create portrait of",
                "that person", "that celebrity", "that politician"
            ],
            HarmAttemptType.EXPLOITATION_ATTEMPT: [
                "nude", "naked", "sexual", "explicit", "porn",
                "adult", "nsfw", "provocative", "seductive"
            ],
            HarmAttemptType.VIOLENCE_ATTEMPT: [
                "violent", "weapon", "fight", "attack",
                "blood", "gore", "harm", "kill", "injury"
            ],
            HarmAttemptType.BIAS_ATTEMPT: [
                "racial", "stereotype", "offensive",
                "racist", "sexist", "discriminatory"
            ],
            HarmAttemptType.DECEPTION_ATTEMPT: [
                "real person", "photorealistic", "real photo",
                "fake this real person"
            ]
        }
    
    async def monitor_generation(self,
                                 user_id: str,
                                 prompt: str,
                                 parameters: Dict) -> Tuple[bool, str]:
        """
        Monitor generation attempt for harmful patterns.
        
        Returns:
            (allow_generation, reason_if_blocked)
        """
        # 1. Check for blocked patterns
        if self._check_blocked_patterns(prompt):
            await self._log_harm_attempt(user_id, prompt, HarmAttemptType.DEEPFAKE_ATTEMPT)
            return False, "Harmful pattern detected in context"
        
        # 2. Rate limit harmful attempts
        if await self._check_harm_rate_limit(user_id):
            return False, "Too many harmful generation attempts - rate limited"
        
        # 3. Check for harmful patterns
        harm_type, severity = self._detect_harm_patterns(prompt)
        if harm_type:
            await self._log_harm_attempt(user_id, prompt, harm_type)
            return False, f"Harmful pattern detected: {harm_type.value}"
        
        # 4. Check parameter safety
        if not self._check_parameter_safety(parameters):
            await self._log_harm_attempt(user_id, prompt, HarmAttemptType.DECEPTION_ATTEMPT)
            return False, "Unsafe parameters detected"
        
        return True, "OK"
    
    def _check_blocked_patterns(self, prompt: str) -> bool:
        """Check against blocked patterns."""
        prompt_lower = prompt.lower()
        for pattern in self.blocked_patterns:
            if pattern in prompt_lower:
                return True
        return False
    
    async def _check_harm_rate_limit(self, user_id: str) -> bool:
        """Rate limit harmful generation attempts."""
        now = datetime.utcnow()
        window_start = now - timedelta(hours=1)
        
        # Clean old attempts
        self.harm_attempts[user_id] = [
            attempt for attempt in self.harm_attempts[user_id]
            if attempt > window_start
        ]
        
        # Check limit (max 10 attempts per hour)
        if len(self.harm_attempts[user_id]) >= 10:
            return True
        
        return False
    
    def _detect_harm_patterns(self, prompt: str) -> Tuple[Optional[HarmAttemptType], int]:
        """
        Detect harmful patterns in prompt.
        
        Returns:
            (harm_type, severity_0_to_10)
        """
        prompt_lower = prompt.lower()
        
        for harm_type, patterns in self.harm_patterns.items():
            for pattern in patterns:
                if pattern in prompt_lower:
                    severity = len([p for p in patterns if p in prompt_lower])
                    return harm_type, min(severity, 10)
        
        return None, 0
    
    def _check_parameter_safety(self, parameters: Dict) -> bool:
        """Check parameters for safety violations."""
        # Check for explicit parameters
        explicit_params = [
            "nudity_level", "explicit_content", "sexual_characteristics",
            "violent_content", "weapon_type", "harm_level"
        ]
        
        for param in explicit_params:
            if param in str(parameters).lower():
                return False
        
        # Check detail level
        if "detail_level" in parameters:
            if parameters["detail_level"] > 0.9:
                return False
        
        return True
    
    async def _log_harm_attempt(self, user_id: str, prompt: str, harm_type: HarmAttemptType):
        """Log harmful generation attempt."""
        attempt_time = datetime.utcnow()
        self.harm_attempts[user_id].append(attempt_time)
        
        log_entry = {
            "user_id": user_id,
            "timestamp": attempt_time.isoformat(),
            "harm_type": harm_type.value,
            "prompt_preview": prompt[:100],
            "blocked": True
        }
        
        # Log locally
        logger.warning(f"Harm attempt detected: {log_entry}")
        
        # Log to Redis if available
        if self.redis:
            try:
                await self.redis.lpush("harm:logs", json.dumps(log_entry))
            except:
                pass
    
    def _load_blocked_patterns(self) -> Set[str]:
        """Load blocked patterns."""
        return {
            # Deepfake attempts
            "looks like", "similar to", "based on",
            "copy the face", "clone appearance", "match to",
            
            # Exploitation
            "nude", "naked", "undressed", "explicit",
            "sexual", "porn", "xxx", "adult content",
            
            # Violence
            "violent", "gore", "blood", "weapon",
            "fight", "attack", "harm", "kill",
            
            # Bias
            "racial stereotype", "offensive caricature",
            "racist depiction", "sexist portrayal",
        }
    
    async def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics."""
        total_attempts = sum(len(logs) for logs in self.harm_attempts.values())
        recent_blocked = sum(
            1 for logs in self.harm_attempts.values()
            for log in logs
            if log > datetime.utcnow() - timedelta(hours=1)
        )
        
        return {
            "total_harm_attempts": total_attempts,
            "recently_blocked": recent_blocked,
            "active_users": len(self.harm_attempts),
            "monitoring_since": datetime.utcnow().isoformat(),
        }
