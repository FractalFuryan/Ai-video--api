"""
Geometry Ethics Guard - Non-negotiable content filtering.
Runs before rendering, before sealing, before storage.
"""
from typing import List, Tuple, Dict, Any
from geometry.spec import GeometryToken, GeometryTokenType


# Forbidden geometry kinds (absolute)
FORBIDDEN_KINDS = {
    # Anatomy
    "face", "head", "skull", "profile",
    "eye", "nose", "mouth", "ear", "lip", "brow",
    "hand", "finger", "palm", "thumb",
    "body", "torso", "chest", "back", "limb",
    "foot", "toe", "heel",
    
    # Biometric proxies
    "oval", "profile", "silhouette", "outline",
    "mask", "visage", "countenance",
    
    # Identity markers
    "portrait", "bust", "statue", "figure",
}

# Forbidden parameter names (biometric-like)
FORBIDDEN_PARAMS = {
    "ratio", "proportion", "spacing", "distance",
    "width", "height", "depth",
    "angle", "tilt",
    "symmetry", "asymmetry",
}

# Forbidden value ranges (biometric ranges in normalized space)
FORBIDDEN_RANGES = [
    # Golden ratio ranges (common in faces)
    (0.6, 0.62),  # Eye spacing
    (0.3, 0.35),  # Nose width ratio
    (0.8, 0.85),  # Face width/height
]


class GeometryEthicsGuard:
    """
    Enforce ethical constraints on geometry generation.
    This is a hard filter - no exceptions.
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violations = []
    
    def validate_tokens(self, tokens: List[GeometryToken]) -> Tuple[bool, List[str]]:
        """
        Validate list of geometry tokens.
        
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        self.violations = []
        
        for i, token in enumerate(tokens):
            self._validate_token(token, i)
        
        valid = len(self.violations) == 0
        
        if not valid and self.strict_mode:
            raise ValueError(f"Ethics validation failed: {self.violations}")
        
        return valid, self.violations.copy()
    
    def _validate_token(self, token: GeometryToken, index: int):
        """Validate a single token."""
        
        # 1. Check forbidden kinds
        if token.kind in FORBIDDEN_KINDS:
            self.violations.append(
                f"Token {index}: Forbidden geometry kind '{token.kind}'"
            )
        
        # 2. Check forbidden parameter names
        for param_name in token.params.keys():
            param_lower = param_name.lower()
            for forbidden in FORBIDDEN_PARAMS:
                if forbidden in param_lower:
                    self.violations.append(
                        f"Token {index}: Parameter '{param_name}' suggests biometric measurement"
                    )
                    break
        
        # 3. Check for biometric value patterns
        if token.token_type == GeometryTokenType.PRIMITIVE:
            self._check_biometric_patterns(token, index)
    
    def _check_biometric_patterns(self, token: GeometryToken, index: int):
        """Check for biometric value patterns in primitives."""
        params = token.params
        
        # Check for width/height/depth combinations (face-like proportions)
        if all(dim in params for dim in ["width", "height", "depth"]):
            w, h, d = params["width"], params["height"], params["depth"]
            
            # Check for face-like aspect ratios
            if h > 0 and w > 0 and d > 0:
                if 0.7 < w/h < 0.9 and 0.1 < d/h < 0.3:
                    self.violations.append(
                        f"Token {index}: Dimensions {w}/{h}/{d} suggest facial proportions"
                    )
    
    def create_validation_report(self, tokens: List[GeometryToken]) -> Dict:
        """Create detailed validation report."""
        is_valid, violations = self.validate_tokens(tokens)
        
        return {
            "valid": is_valid,
            "violations": violations,
            "token_count": len(tokens),
            "token_types": [t.token_type.value for t in tokens],
            "kinds": [t.kind for t in tokens],
            "strict_mode": self.strict_mode,
            "checks_performed": [
                "forbidden_kinds",
                "forbidden_params", 
                "biometric_patterns",
            ]
        }


# Global instance for convenience
guard = GeometryEthicsGuard(strict_mode=True)


def validate_geometry(tokens: List[GeometryToken]) -> None:
    """
    Convenience function for strict validation.
    
    Raises:
        ValueError: If validation fails
    """
    is_valid, violations = guard.validate_tokens(tokens)
    if not is_valid:
        raise ValueError(f"Geometry validation failed: {violations}")


def safe_validate_geometry(tokens: List[GeometryToken]) -> Dict:
    """
    Safe validation that returns report instead of raising.
    """
    return guard.create_validation_report(tokens)
