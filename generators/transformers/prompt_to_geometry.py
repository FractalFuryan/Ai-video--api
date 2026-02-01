"""
Deterministic prompt to geometry transformer.
No ML. No embeddings. No randomness.
"""
import re
import hashlib
from typing import List, Dict, Tuple
from geometry.spec import GeometryToken, GeometryTokenType, create_primitive


# Canonical mapping - extend carefully
PROMPT_PATTERNS = {
    # Primitives
    r"\b(cube|cubic|box)\b": ("cube", {"size": 1.0}),
    r"\b(sphere|ball|orb|globe)\b": ("sphere", {"radius": 1.0}),
    r"\b(cylinder|tube|pipe|column)\b": ("cylinder", {"radius": 0.5, "height": 1.0}),
    r"\b(cone|pyramid|pointy)\b": ("cone", {"radius": 0.5, "height": 1.0}),
    r"\b(torus|donut|ring)\b": ("torus", {"major_radius": 1.0, "minor_radius": 0.3}),
    r"\b(plane|flat|surface)\b": ("plane", {"width": 1.0, "height": 1.0}),
    
    # Modifiers (affect parameters)
    r"\b(large|big|huge)\b": ("scale", {"factor": 2.0}),
    r"\b(small|tiny|little)\b": ("scale", {"factor": 0.5}),
    r"\b(wide|broad)\b": ("scale", {"x": 2.0, "y": 1.0, "z": 1.0}),
    r"\b(tall|high)\b": ("scale", {"x": 1.0, "y": 2.0, "z": 1.0}),
    
    # Transforms
    r"\b(rotate|spin|twirl)\b": ("rotate_y", {"angle": 45.0}),
    r"\b(tilt|lean)\b": ("rotate_x", {"angle": 15.0}),
    r"\b(move|shift|translate)\b": ("translate", {"x": 1.0, "y": 0.0, "z": 0.0}),
}

# Stop words that indicate invalid content
STOP_PATTERNS = [
    r"\b(face|head|eye|nose|mouth|ear|body|hand|finger)\b",
    r"\b(person|human|animal|creature|character)\b",
    r"\b(portrait|selfie|photo|picture|image)\b",
]


def parse_prompt(prompt: str) -> List[GeometryToken]:
    """
    Parse prompt into geometry tokens.
    Deterministic and rule-based.
    
    Args:
        prompt: Natural language prompt
        
    Returns:
        List of geometry tokens
        
    Raises:
        ValueError: If prompt contains stop words or produces no geometry
    """
    prompt_lower = prompt.lower().strip()
    
    # 1. Check for stop words
    for pattern in STOP_PATTERNS:
        if re.search(pattern, prompt_lower):
            raise ValueError(f"Prompt contains disallowed content: {pattern}")
    
    # 2. Extract tokens
    extracted = []
    modifiers = []
    
    for pattern, (kind, params) in PROMPT_PATTERNS.items():
        if re.search(pattern, prompt_lower):
            if kind in ["cube", "sphere", "cylinder", "cone", "torus", "plane"]:
                # It's a primitive
                extracted.append((kind, params))
            else:
                # It's a modifier/transform
                modifiers.append((kind, params))
    
    # 3. Create geometry tokens
    tokens = []
    
    for primitive_kind, base_params in extracted:
        # Create base primitive
        token = create_primitive(primitive_kind, **base_params)
        tokens.append(token)
    
    # 4. Apply modifiers to the last primitive
    if tokens and modifiers:
        last_token = tokens[-1]
        
        for mod_kind, mod_params in modifiers:
            if mod_kind == "scale":
                # Create scale transform token
                scale_token = GeometryToken(
                    token_type=GeometryTokenType.TRANSFORM,
                    kind="scale",
                    params=mod_params,
                    bounds=last_token.bounds,
                )
                tokens.append(scale_token)
            elif mod_kind.startswith("rotate"):
                # Create rotation token
                rotate_token = GeometryToken(
                    token_type=GeometryTokenType.TRANSFORM,
                    kind=mod_kind,
                    params=mod_params,
                    bounds=last_token.bounds,
                )
                tokens.append(rotate_token)
            elif mod_kind == "translate":
                # Create translation token
                translate_token = GeometryToken(
                    token_type=GeometryTokenType.TRANSFORM,
                    kind=mod_kind,
                    params=mod_params,
                    bounds=last_token.bounds,
                )
                tokens.append(translate_token)
    
    # 5. Ensure we have at least one token
    if not tokens:
        raise ValueError("Prompt produced no recognizable geometry")
    
    return tokens


def analyze_prompt_complexity(prompt: str) -> Dict[str, any]:
    """
    Analyze prompt complexity for logging/monitoring.
    """
    prompt_lower = prompt.lower()
    
    # Count recognized patterns
    pattern_counts = {}
    for pattern in PROMPT_PATTERNS:
        matches = len(re.findall(pattern, prompt_lower))
        if matches > 0:
            pattern_name = pattern.replace(r"\b", "").replace("(", "").replace(")", "")
            pattern_counts[pattern_name] = matches
    
    # Check for potential issues
    warnings = []
    for stop_pattern in STOP_PATTERNS:
        if re.search(stop_pattern, prompt_lower):
            warnings.append(f"Matched stop pattern: {stop_pattern}")
    
    return {
        "word_count": len(prompt.split()),
        "recognized_patterns": pattern_counts,
        "warnings": warnings,
        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16]
    }
