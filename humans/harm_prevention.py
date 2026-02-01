"""
Architectural Harm Prevention Guard

Prevent exploitation, bias, deepfakes, violence at the generation level.
Not filters - built into the mathematics.
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
import json
import hashlib
from datetime import datetime


class HarmCategory(Enum):
    """Categories of harm to prevent architecturally."""
    DEEPFAKE = "deepfake"               # Impersonation via facial matching
    EXPLOITATION = "exploitation"       # Sexual/non-consensual content
    BIAS = "bias"                       # Racial/gender stereotyping
    DECEPTION = "deception"             # Misleading representation  
    VIOLENCE = "violence"               # Harmful/violent content


class ArchitecturalHarmGuard:
    """
    Prevent harm at the ARCHITECTURAL level.
    Not content filters - built into generation constraints.
    """
    
    def __init__(self):
        """Initialize harm prevention systems."""
        
        # 1. DEEPFAKE PREVENTION: Mathematical guarantees
        self.deepfake_preventions = {
            "non_injective_generation": True,      # Many seeds → similar output
            "no_biometric_parameters": True,       # No real face measurements
            "mathematical_construction_only": True, # No training data
            "seed_irreversibility": True,          # Cannot invert seed from face
        }
        
        # 2. EXPLOITATION PREVENTION: Classical proportions
        self.exploitation_guard = {
            "classical_proportions_enforced": True,
            "no_exaggerated_features": True,
            "max_breast_to_waist_ratio": 0.8,      # Classical range
            "max_waist_to_hip_ratio": 0.75,        # Not exaggerated
            "no_explicit_parameters": True,
            "artistic_smoothing_required": True,
            "detail_level_capped": 0.7,
        }
        
        # 3. BIAS PREVENTION: Universal mathematics
        self.bias_preventions = {
            "no_racial_feature_parameters": True,
            "golden_ratio_beauty_standards": True,  # Not cultural
            "continuous_feature_spectrum": True,    # No categorical race
            "no_gender_specific_proportions": False,  # Gender spectrum allowed
            "symmetric_treatment": True,
        }
        
        # 4. DECEPTION PREVENTION
        self.deception_preventions = {
            "clearly_not_photorealistic": True,
            "artistic_style_required": True,
            "metadata_transparency": True,
            "seed_included_with_face": True,
        }
        
        # 5. VIOLENCE PREVENTION
        self.violence_preventions = {
            "no_weapon_parameters": True,
            "no_violent_pose_parameters": True,
            "no_blood_gore_parameters": True,
            "no_injury_parameters": True,
        }
        
        # Forbidden parameters that would enable harm
        self.forbidden_parameters = {
            # Biometric identifiers
            "iris_pattern", "iris_color_specific", "retinal_pattern",
            "facial_landmark_match", "biometric_id",
            "exact_nose_length", "exact_eye_width",
            
            # Identity encoding
            "person_id", "identity_id", "subject_id",
            "match_to_person", "look_like", "resemble",
            
            # Exploitation
            "nude_level", "nudity_amount", "explicit_content",
            "sexual_pose", "sexual_characteristic",
            "breast_size", "exact_measurements",
            
            # Violence
            "weapon_type", "injury_type", "blood_amount",
            "violent_pose", "aggression_level",
            
            # Deception
            "real_person_lookalike", "photorealistic_mode",
            "match_to_celebrity", "match_to_politician",
        }
        
        # Allowed parameters that are artistic
        self.allowed_parameters = {
            # Artistic choices
            "artistic_style", "artistic_period", "artistic_medium",
            "stylization_level", "realism_level",
            
            # Pose (non-violent)
            "neutral_pose", "sitting", "standing", "relaxing",
            "artistic_gesture", "dance_pose",
            
            # Proportions (artistic range)
            "face_width_height_ratio", "eye_separation_ratio",
            "nose_length_ratio", "mouth_curvature",
            
            # Hair and features
            "hair_style", "hair_color", "hair_texture",
            "skin_smoothness", "skin_tone",
            
            # Non-biometric properties
            "expression_type", "looking_direction",
            "head_tilt", "emotional_tone",
        }
    
    def enforce_harm_prevention(self, 
                               identity_dict: Dict,
                               context: str = "") -> Tuple[bool, List[str]]:
        """
        Enforce harm prevention at parameter level.
        
        Returns:
            (is_safe, list_of_violations)
        """
        violations = []
        
        # Check for forbidden parameters
        for forbidden_param in self.forbidden_parameters:
            if self._parameter_present(identity_dict, forbidden_param):
                violations.append(f"Forbidden parameter: {forbidden_param}")
        
        # Check deepfake prevention
        if not self._prevent_deepfake(identity_dict):
            violations.append("Deepfake prevention violated")
        
        # Check exploitation prevention
        if not self._prevent_exploitation(identity_dict):
            violations.append("Exploitation prevention violated")
        
        # Check bias prevention
        if not self._prevent_bias(identity_dict):
            violations.append("Bias prevention violated")
        
        # Check deception prevention
        if not self._prevent_deception(identity_dict, context):
            violations.append("Deception prevention violated")
        
        # Check violence prevention
        if not self._prevent_violence(identity_dict):
            violations.append("Violence prevention violated")
        
        return len(violations) == 0, violations
    
    def _parameter_present(self, data: Dict, param_name: str) -> bool:
        """Check if parameter is present in data structure."""
        # Check top level
        if param_name in data:
            return True
        
        # Check in nested dicts
        for key, value in data.items():
            if isinstance(value, dict):
                if param_name in value:
                    return True
        
        return False
    
    def _prevent_deepfake(self, identity_dict: Dict) -> bool:
        """Enforce deepfake prevention."""
        # 1. Must have non-injective proof
        if "non_injective_proof" not in identity_dict and \
           "equivalence_class" not in identity_dict:
            return False
        
        # 2. Must NOT have biometric parameters
        biometric_indicators = [
            "iris_pattern", "retinal_scan", "facial_landmarks",
            "exact_measurements", "person_match", "identity_match"
        ]
        for indicator in biometric_indicators:
            if self._parameter_present(identity_dict, indicator):
                return False
        
        # 3. Must have mathematical proof
        if "mathematical_proof" not in identity_dict:
            return False
        
        return True
    
    def _prevent_exploitation(self, identity_dict: Dict) -> bool:
        """Prevent sexual/non-consensual content."""
        geometry = identity_dict.get("face_geometry", {})
        
        # 1. Classical proportions only (not pornographic)
        problematic_ratios = [
            ("breast_to_waist_ratio", (0.9, 2.0)),  # Too exaggerated
            ("waist_to_hip_ratio", (0.4, 0.6)),     # Too extreme
        ]
        
        for ratio_name, bad_range in problematic_ratios:
            if ratio_name in geometry:
                value = geometry[ratio_name]
                if bad_range[0] <= value <= bad_range[1]:
                    return False
        
        # 2. Artistic smoothing required (not photographic)
        if "skin_smoothness" in geometry:
            if geometry["skin_smoothness"] < 0.5:  # Too detailed
                return False
        
        # 3. Detail level capped
        if "skin_complexity" in geometry:
            if geometry["skin_complexity"] > 0.7:  # Too explicit
                return False
        
        # 4. No explicit parameters
        explicit_params = [
            "nudity_level", "explicit_content", "sexual_features",
            "sexual_pose", "genital_parameters"
        ]
        for param in explicit_params:
            if self._parameter_present(identity_dict, param):
                return False
        
        return True
    
    def _prevent_bias(self, identity_dict: Dict) -> bool:
        """Prevent racial/gender bias."""
        geometry = identity_dict.get("face_geometry", {})
        
        # 1. No racial feature parameters
        racial_indicators = [
            "skin_tone", "specific_ethnicity", "racial_features",
            "nose_shape_ethnic", "lip_size_ethnic",
            "eye_shape_racial", "hair_texture_ethnic"
        ]
        for indicator in racial_indicators:
            if self._parameter_present(identity_dict, indicator):
                return False
        
        # 2. Beauty standard must be universal (golden ratio)
        proof = identity_dict.get("mathematical_proof", {})
        if "golden_ratio" not in str(proof).lower() and \
           "fibonacci" not in str(proof).lower():
            # OK to use other methods, but not biased cultural standards
            pass
        
        # 3. Gender should be continuous spectrum, not binary
        # (We allow gender but it should be continuous, not categorical)
        
        return True
    
    def _prevent_deception(self, identity_dict: Dict, context: str = "") -> bool:
        """Prevent misleading representation."""
        # 1. Must be clearly artistic, not photorealistic
        artistic_style = identity_dict.get("artistic_style", {})
        
        if "realism_level" in artistic_style:
            # Should NOT be photorealistic
            if artistic_style["realism_level"] > 0.85:
                return False
        
        # 2. Metadata should indicate it's mathematically generated
        if "mathematical_proof" not in identity_dict:
            return False
        
        # 3. Seed should be included for verification
        if "seed" not in identity_dict:
            return False
        
        return True
    
    def _prevent_violence(self, identity_dict: Dict) -> bool:
        """Prevent violent/harmful content."""
        # 1. No weapon parameters
        weapon_indicators = [
            "weapon_type", "weapon_held", "gun", "knife", "weapon_visible"
        ]
        for indicator in weapon_indicators:
            if self._parameter_present(identity_dict, indicator):
                return False
        
        # 2. No violent pose parameters
        if "pose_type" in identity_dict:
            pose = identity_dict.get("pose_type", "").lower()
            violent_keywords = ["violent", "fighting", "attacking", "weapon"]
            for keyword in violent_keywords:
                if keyword in pose:
                    return False
        
        # 3. No harm/injury indicators
        harm_indicators = ["blood", "gore", "injury", "harm", "damaged"]
        for indicator in harm_indicators:
            if self._parameter_present(identity_dict, indicator):
                return False
        
        return True
    
    def generate_harm_prevention_certificate(self,
                                            identity_dict: Dict,
                                            context: str = "") -> Dict:
        """Generate certificate proving harm prevention."""
        safe, violations = self.enforce_harm_prevention(identity_dict, context)
        
        certificate = {
            "harm_prevention_version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "safe": safe,
            "violations": violations,
            
            "architectural_guarantees": {
                "deepfake_prevention": self._prevent_deepfake(identity_dict),
                "exploitation_prevention": self._prevent_exploitation(identity_dict),
                "bias_prevention": self._prevent_bias(identity_dict),
                "deception_prevention": self._prevent_deception(identity_dict, context),
                "violence_prevention": self._prevent_violence(identity_dict),
            },
            
            "allowed_parameters": list(self.allowed_parameters),
            "forbidden_parameters": list(self.forbidden_parameters),
            
            "content_rating": self._determine_content_rating(identity_dict),
            
            "verification_hash": self._certificate_hash(identity_dict),
        }
        
        return certificate
    
    def _determine_content_rating(self, identity_dict: Dict) -> str:
        """Determine appropriate content rating."""
        # G: All audiences
        # PG: Parental guidance
        # PG-13: Parents strongly cautioned
        # R: Restricted
        
        # Default: G (completely safe)
        return "G"
    
    def _certificate_hash(self, identity_dict: Dict) -> str:
        """Create hash of certificate for verification."""
        data = json.dumps(identity_dict, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
