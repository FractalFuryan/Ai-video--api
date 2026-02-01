"""
Artistic Figure Primitives for HarmonyØ4

Enables human-like form generation through SEALED, non-parametric figure types.
Think: mannequin, artist's wooden figure, dance pose reference, sculpture.

ETHICAL ARCHITECTURE:
- No facial features (smooth head geometry)
- No skin texture parameters
- No identity-encoding proportions
- Fixed stylization levels prevent photorealism
- Poseable, but not personifiable

This is how artists have depicted humans for millennia: through abstraction,
gesture, form, and pose - NOT photorealistic identity replication.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
import hashlib


class FigureStyle(Enum):
    """Sealed figure styles - each prevents photorealism through different abstraction"""
    MANNEQUIN = "mannequin"          # Smooth, featureless retail display figure
    WIREFRAME = "wireframe"          # Line-based armature (artist reference)
    SILHOUETTE = "silhouette"        # Solid shadow form (no features)
    WOODEN_ARTIST = "wooden_artist"  # Articulated wooden art model
    SCULPT_BLOCK = "sculpt_block"    # Rough blocked-out sculptor's maquette
    GESTURE = "gesture"              # Minimal expressive line form
    CUBIST = "cubist"                # Geometric faceted abstraction


class FigurePose(Enum):
    """Named poses - deterministic, non-generative"""
    STANDING_NEUTRAL = "standing_neutral"
    SITTING_CROSS_LEGGED = "sitting_cross_legged"
    WALKING_FORWARD = "walking_forward"
    RUNNING = "running"
    REACHING_UP = "reaching_up"
    KNEELING = "kneeling"
    DANCING_ARABESQUE = "dancing_arabesque"
    THINKING = "thinking"  # Rodin-style
    DEFENSIVE_CROUCH = "defensive_crouch"
    TRIUMPHANT_ARMS_RAISED = "triumphant_arms_raised"
    RECLINING = "reclining"
    MEDITATION_LOTUS = "meditation_lotus"


@dataclass(frozen=True)
class ArtisticFigure:
    """
    A sealed human-like figure for artistic composition.
    
    NO PARAMETERS FOR:
    - Face shape or features
    - Skin color or texture  
    - Body proportions (fixed per style)
    - Identity markers
    
    YES PARAMETERS FOR:
    - Pose (from enum)
    - Style (from enum)
    - Scale
    - Orientation
    """
    style: FigureStyle
    pose: FigurePose
    scale: float = 1.0
    rotation_y: float = 0.0  # Simple Y-axis rotation only
    
    def __post_init__(self):
        """Validate constraints"""
        if not 0.1 <= self.scale <= 10.0:
            raise ValueError("Scale must be between 0.1 and 10.0")
        if not 0.0 <= self.rotation_y <= 360.0:
            raise ValueError("Rotation must be between 0 and 360 degrees")
    
    @property
    def uid(self) -> str:
        """Deterministic unique identifier"""
        content = f"{self.style.value}:{self.pose.value}:{self.scale:.3f}:{self.rotation_y:.1f}"
        return f"fig_{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    
    def to_geometry_tokens(self) -> List[dict]:
        """
        Convert to base geometry primitives.
        
        Each FigureStyle has a FIXED geometric construction.
        No parametric variation - only pose and transform.
        """
        # This is where we'd construct the actual geometry
        # For now, return the specification
        return [{
            "type": "artistic_figure",
            "uid": self.uid,
            "style": self.style.value,
            "pose": self.pose.value,
            "transform": {
                "scale": self.scale,
                "rotation_y": self.rotation_y
            }
        }]


class FigureEthicsGuard:
    """Validates that figure usage remains within artistic bounds"""
    
    FORBIDDEN_DESCRIPTORS = {
        # Identity markers
        "celebrity", "politician", "person", "portrait", "selfie",
        "realistic", "photorealistic", "lifelike",
        
        # Facial features
        "face", "eyes", "nose", "mouth", "lips", "cheeks", "jaw",
        "smile", "frown", "expression",
        
        # Identity-encoding attributes
        "race", "ethnicity", "age", "gender", "identity",
        "skin", "texture", "pores", "wrinkles",
        
        # Problematic contexts
        "nude", "naked", "explicit", "sexual",
        "violence", "victim", "corpse"
    }
    
    @staticmethod
    def validate_prompt(prompt: str) -> Tuple[bool, str]:
        """Check if prompt stays within artistic figure bounds"""
        prompt_lower = prompt.lower()
        
        for forbidden in FigureEthicsGuard.FORBIDDEN_DESCRIPTORS:
            if forbidden in prompt_lower:
                return False, f"Forbidden descriptor: '{forbidden}'. Use abstract artistic terms instead."
        
        return True, "OK"
    
    @staticmethod
    def allowed_prompt_examples() -> List[str]:
        """Examples of valid artistic figure prompts"""
        return [
            "mannequin figure in dancing pose, small scale",
            "wireframe figure reaching upward, rotated 45 degrees",
            "silhouette figure in meditation pose",
            "wooden artist figure in walking motion",
            "cubist figure, triumphant pose, large scale",
            "gesture figure in running pose, subtle rotation"
        ]


def parse_figure_prompt(prompt: str) -> ArtisticFigure:
    """
    Deterministic prompt parser for artistic figures.
    
    Example prompts:
        "mannequin figure standing"
        "wireframe dancer, arabesque pose"
        "silhouette walking, rotated 90 degrees"
    """
    # Ethics check first
    is_valid, msg = FigureEthicsGuard.validate_prompt(prompt)
    if not is_valid:
        raise ValueError(f"Ethics violation: {msg}")
    
    prompt_lower = prompt.lower()
    
    # Parse style
    style = FigureStyle.MANNEQUIN  # default
    for s in FigureStyle:
        if s.value.replace("_", " ") in prompt_lower:
            style = s
            break
    
    # Parse pose
    pose = FigurePose.STANDING_NEUTRAL  # default
    for p in FigurePose:
        if p.value.replace("_", " ") in prompt_lower:
            pose = p
            break
    
    # Parse scale
    scale = 1.0
    if "small" in prompt_lower:
        scale = 0.5
    elif "large" in prompt_lower:
        scale = 2.0
    elif "tiny" in prompt_lower:
        scale = 0.2
    
    # Parse rotation (simple)
    rotation = 0.0
    if "rotated" in prompt_lower or "rotation" in prompt_lower:
        # Extract number if present
        words = prompt_lower.split()
        for i, word in enumerate(words):
            if "degree" in word and i > 0:
                try:
                    rotation = float(words[i-1])
                except:
                    rotation = 45.0  # default rotation
                break
    
    return ArtisticFigure(
        style=style,
        pose=pose,
        scale=scale,
        rotation_y=rotation
    )


if __name__ == "__main__":
    # Test cases
    print("=== Artistic Figure Primitives ===\n")
    
    # Valid examples
    examples = [
        "mannequin figure standing",
        "wireframe dancer in arabesque pose",
        "silhouette walking forward, rotated 90 degrees",
        "wooden artist figure, thinking pose, small scale",
        "cubist figure triumphant, large"
    ]
    
    print("VALID PROMPTS:")
    for prompt in examples:
        fig = parse_figure_prompt(prompt)
        print(f"  '{prompt}'")
        print(f"    -> {fig.style.value}, {fig.pose.value}, scale={fig.scale}, rot={fig.rotation_y}°")
        print(f"    -> UID: {fig.uid}\n")
    
    # Invalid examples
    invalid = [
        "realistic person standing",
        "mannequin with facial features",
        "nude figure",
        "portrait of celebrity"
    ]
    
    print("\nINVALID PROMPTS:")
    for prompt in invalid:
        try:
            fig = parse_figure_prompt(prompt)
            print(f"  '{prompt}' - SHOULD HAVE FAILED")
        except ValueError as e:
            print(f"  '{prompt}' - ✓ BLOCKED: {e}")
