"""
Complete API documentation for HarmonyØ4 Geometry Generator.
Auto-generated documentation for all endpoints and system components.
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class APIStatus(Enum):
    """API endpoint status."""
    ACTIVE = "active"
    BETA = "beta"
    DEPRECATED = "deprecated"


class EndpointDoc(BaseModel):
    """Documentation for a single endpoint."""
    method: str
    path: str
    description: str
    status: APIStatus
    parameters: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    example: Optional[Dict[str, Any]] = None


class APIDocumentation:
    """Complete API documentation generator."""
    
    VERSION = "1.0.0"
    SYSTEM_NAME = "HarmonyØ4 Ethical Geometry Generator"
    
    @staticmethod
    def get_overview() -> Dict[str, Any]:
        """Get system overview."""
        return {
            "system": APIDocumentation.SYSTEM_NAME,
            "version": APIDocumentation.VERSION,
            "description": "Category-defining ethical geometry generation system. Generates structure, not pixels.",
            "tagline": "Category exit: We don't generate pixels. We generate sealed spatial programs.",
            "architecture": {
                "phases": [
                    {"id": "G0", "name": "Formal Geometry Spec", "status": "complete", "file": "geometry/spec.py"},
                    {"id": "G1", "name": "Deterministic Prompt Parser", "status": "complete", "file": "generators/transformers/prompt_to_geometry.py"},
                    {"id": "G2", "name": "Ethical Structural Guard", "status": "complete", "file": "ethics/constraints.py"},
                    {"id": "G3", "name": "Temporal Animation System", "status": "complete", "file": "geometry/temporal.py"},
                    {"id": "G4", "name": "H4MK Container Integration", "status": "complete", "file": "container/geometry_container.py"},
                    {"id": "G5", "name": "WebGL Viewer & API", "status": "complete", "file": "api/routes/geometry.py"},
                ],
                "security": {
                    "no_pixels": True,
                    "no_identity": True,
                    "deterministic": True,
                    "auditable": True,
                    "sealed_containers": True,
                }
            },
            "deployment_date": "2026-02-01",
            "repository": "https://github.com/FractalFuryan/Ai-video--api"
        }
    
    @staticmethod
    def get_endpoints() -> List[EndpointDoc]:
        """Get all API endpoints."""
        return [
            EndpointDoc(
                method="POST",
                path="/geometry/generate",
                description="Generate geometry from natural language prompt. Core endpoint for ethical geometry generation.",
                status=APIStatus.ACTIVE,
                parameters={
                    "prompt": {
                        "type": "string",
                        "required": True,
                        "description": "Natural language prompt describing geometry",
                        "example": "rotating cubes and pulsating spheres"
                    },
                    "duration_seconds": {
                        "type": "number",
                        "required": False,
                        "default": 5.0,
                        "description": "Animation duration in seconds"
                    },
                    "fps": {
                        "type": "integer",
                        "required": False,
                        "default": 30,
                        "description": "Frames per second for animation"
                    }
                },
                response={
                    "tokens": "List of geometry tokens",
                    "validation_report": "Ethics validation results",
                    "temporal": "Temporal sequences (if animation requested)",
                    "summary": "Generation summary and metadata"
                },
                example={
                    "request": {
                        "prompt": "rotating cubes and spheres",
                        "duration_seconds": 5.0,
                        "fps": 30
                    },
                    "response": {
                        "tokens": [
                            {"token_type": "primitive", "kind": "cube", "uid": "g04cd1463828ada00"},
                            {"token_type": "primitive", "kind": "sphere", "uid": "g192696b314068a9c"}
                        ],
                        "validation_report": {"valid": True, "token_count": 2},
                        "summary": {"token_count": 2, "has_animation": True}
                    }
                }
            ),
            EndpointDoc(
                method="GET",
                path="/geometry/viewer/{data_hash}",
                description="Interactive WebGL viewer for generated geometry. Client-side rendering.",
                status=APIStatus.ACTIVE,
                parameters={
                    "data_hash": {
                        "type": "string",
                        "required": True,
                        "description": "Data hash from generation response",
                        "example": "abc123def456"
                    }
                },
                response={
                    "content_type": "text/html",
                    "description": "HTML page with Three.js WebGL viewer"
                }
            ),
            EndpointDoc(
                method="GET",
                path="/geometry/primitives",
                description="List all available geometry primitives and transforms",
                status=APIStatus.ACTIVE,
                response={
                    "primitives": ["cube", "sphere", "cylinder", "cone", "torus", "plane"],
                    "transforms": ["translate", "rotate_x", "rotate_y", "rotate_z", "scale"],
                    "description": "Canonical geometry tokens for ethical generation"
                }
            ),
            EndpointDoc(
                method="POST",
                path="/geometry/test-parse",
                description="Debug endpoint for prompt parsing (development/testing)",
                status=APIStatus.BETA,
                parameters={
                    "prompt": {
                        "type": "string",
                        "required": True,
                        "description": "Prompt to test"
                    }
                },
                response={
                    "prompt": "Original prompt",
                    "tokens_generated": "Number of tokens",
                    "token_kinds": "List of token kinds",
                    "analysis": "Complexity analysis",
                    "validation": "Ethics validation report"
                }
            ),
            EndpointDoc(
                method="GET",
                path="/geometry/health",
                description="System health check and status",
                status=APIStatus.ACTIVE,
                response={
                    "status": "ok",
                    "system": "HarmonyØ4 Geometry Generator (G0-G5)",
                    "capabilities": [
                        "deterministic_prompt_parsing",
                        "ethical_validation",
                        "temporal_animation",
                        "container_integration",
                        "webgl_viewing"
                    ],
                    "version": "1.0.0"
                }
            )
        ]
    
    @staticmethod
    def get_ethical_guarantees() -> Dict[str, Any]:
        """Get ethical guarantees and constraints."""
        return {
            "guarantees": [
                {
                    "id": "no-pixels",
                    "name": "No Pixel Generation",
                    "description": "System generates only geometry tokens, never pixel data",
                    "enforcement": "Architecture-level guarantee",
                    "impact": "Cannot generate photorealistic content or deepfakes",
                },
                {
                    "id": "no-identity",
                    "name": "No Facial/Identity Geometry",
                    "description": "Hard-coded blocklist prevents generation of faces, bodies, or recognizable people",
                    "enforcement": "Ethics guard with forbidden kinds list",
                    "impact": "Cannot encode human identity or biometric data",
                },
                {
                    "id": "no-biometrics",
                    "name": "No Biometric Parameters",
                    "description": "Parameter validation prevents encoding of facial proportions, spacing, or symmetry",
                    "enforcement": "Parameter name and value validation",
                    "impact": "Cannot circumvent identity checks via proportions",
                },
                {
                    "id": "deterministic",
                    "name": "Deterministic Generation",
                    "description": "Same input always produces same output (no randomness, no ML)",
                    "enforcement": "Rule-based parsing with no stochastic components",
                    "impact": "Auditable, reproducible, verifiable generations",
                },
                {
                    "id": "sealed-auditable",
                    "name": "Sealed & Auditable",
                    "description": "All geometry sealed in H4MK containers with cryptographic hashing",
                    "enforcement": "Container integration with deterministic hashing",
                    "impact": "Complete provenance tracking and tamper evidence",
                },
            ],
            "forbidden_patterns": {
                "anatomy": ["face", "eye", "nose", "mouth", "ear", "hand", "finger", "body", "head"],
                "identity": ["portrait", "profile", "silhouette", "character", "person", "human"],
                "biometric": ["ratio", "spacing", "symmetry", "proportion", "distance"],
                "photographic": ["photo", "image", "picture", "selfie", "photograph"]
            },
            "allowed_geometry": {
                "primitives": ["cube", "sphere", "cylinder", "cone", "torus", "plane"],
                "transforms": ["rotate", "translate", "scale"],
                "temporal": ["keyframe animations", "interpolation"],
                "structural": ["grouping", "hierarchies", "compositions"]
            }
        }
    
    @staticmethod
    def get_quickstart() -> Dict[str, Any]:
        """Get quick start examples."""
        return {
            "curl": {
                "description": "cURL examples for API testing",
                "examples": [
                    {
                        "name": "Generate Geometry",
                        "code": """curl -X POST http://localhost:8000/geometry/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "dancing geometric shapes",
    "duration_seconds": 5.0,
    "fps": 30
  }'"""
                    },
                    {
                        "name": "View Geometry",
                        "code": """# Get data_hash from generation response
curl http://localhost:8000/geometry/viewer/{data_hash}"""
                    },
                    {
                        "name": "List Primitives",
                        "code": """curl http://localhost:8000/geometry/primitives"""
                    }
                ]
            },
            "python": {
                "description": "Python SDK examples",
                "examples": [
                    {
                        "name": "Basic Generation",
                        "code": """from geometry.spec import create_primitive
from generators.transformers.prompt_to_geometry import parse_prompt
from ethics.constraints import safe_validate_geometry

# Parse prompt to tokens
tokens = parse_prompt("rotating cube and sphere")

# Validate ethics
report = safe_validate_geometry(tokens)
print(f"Valid: {report['valid']}")
print(f"Tokens: {report['token_count']}")

# Create animation
from geometry.temporal import TemporalGeometryGenerator
gen = TemporalGeometryGenerator(fps=30)
sequences = gen.create_animation(tokens, duration_seconds=5.0)
print(f"Animation sequences: {len(sequences)}")"""
                    }
                ]
            },
            "javascript": {
                "description": "JavaScript/TypeScript examples",
                "examples": [
                    {
                        "name": "Fetch API",
                        "code": """async function generateGeometry(prompt) {
  const response = await fetch('http://localhost:8000/geometry/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      prompt: prompt,
      duration_seconds: 5.0
    })
  });
  
  const data = await response.json();
  
  // Open viewer
  window.open(`/geometry/viewer/${data.container_hash}`);
  
  return data;
}

// Usage
generateGeometry("rotating cubes and spheres");"""
                    }
                ]
            }
        }


# Export complete documentation
def generate_complete_documentation() -> Dict[str, Any]:
    """Generate complete API documentation."""
    return {
        "overview": APIDocumentation.get_overview(),
        "endpoints": [ep.dict() for ep in APIDocumentation.get_endpoints()],
        "ethics": APIDocumentation.get_ethical_guarantees(),
        "quickstart": APIDocumentation.get_quickstart(),
        "version": APIDocumentation.VERSION,
        "generated_at": datetime.utcnow().isoformat(),
    }


# Singleton instance
COMPLETE_DOCS = generate_complete_documentation()
