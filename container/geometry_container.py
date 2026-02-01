"""
Geometry container integration for HarmonyØ4.
Integrates geometry data into H4MK containers.
"""
import json
from typing import List, Dict, Any, Optional
from geometry.spec import GeometryToken
from geometry.temporal import TemporalSequence, export_temporal_data


class GeometryContainer:
    """Integrate geometry data into H4MK containers."""
    
    # Chunk types for geometry data
    CHUNK_GEOMETRY = b"GEOM"  # Geometry tokens
    CHUNK_TEMPORAL = b"TEMP"  # Temporal sequences
    CHUNK_GEOMETRY_META = b"GMET"  # Geometry metadata
    
    def __init__(self, h4mk_container):
        self.container = h4mk_container
    
    def add_geometry_tokens(self, tokens: List[GeometryToken]) -> str:
        """
        Add geometry tokens to container.
        
        Returns:
            Hash of the geometry data
        """
        # Convert to serializable format
        geometry_data = [t.to_dict() for t in tokens]
        
        # Serialize as JSON for compatibility
        json_data = json.dumps(geometry_data, separators=(",", ":")).encode()
        
        # Add to container
        self.container.add_chunk(self.CHUNK_GEOMETRY, json_data)
        
        # Add metadata
        metadata = {
            "token_count": len(tokens),
            "token_types": list(set(t.token_type.value for t in tokens)),
            "primitive_kinds": list(set(t.kind for t in tokens 
                                      if t.token_type.value == "primitive")),
            "format_version": "h4-geometry-v1"
        }
        
        self.container.add_chunk(
            self.CHUNK_GEOMETRY_META,
            json.dumps(metadata, separators=(",", ":")).encode()
        )
        
        # Return data hash for reference
        import hashlib
        return hashlib.sha256(json_data).hexdigest()[:16]
    
    def add_temporal_sequences(self, sequences: List[TemporalSequence]) -> str:
        """
        Add temporal sequences to container.
        
        Returns:
            Hash of the temporal data
        """
        # Convert to serializable format
        temporal_data = [s.to_dict() for s in sequences]
        
        # Serialize as JSON
        json_data = json.dumps(temporal_data, separators=(",", ":")).encode()
        
        # Add to container
        self.container.add_chunk(self.CHUNK_TEMPORAL, json_data)
        
        # Return data hash
        import hashlib
        return hashlib.sha256(json_data).hexdigest()[:16]
    
    def get_geometry_tokens(self) -> List[GeometryToken]:
        """Retrieve geometry tokens from container."""
        json_data = self.container.get_chunk(self.CHUNK_GEOMETRY)
        if not json_data:
            return []
        
        geometry_list = json.loads(json_data.decode())
        tokens = []
        
        for item in geometry_list:
            token = GeometryToken.from_dict(item)
            tokens.append(token)
        
        return tokens
    
    def get_temporal_sequences(self) -> List[TemporalSequence]:
        """Retrieve temporal sequences from container."""
        json_data = self.container.get_chunk(self.CHUNK_TEMPORAL)
        if not json_data:
            return []
        
        temporal_list = json.loads(json_data.decode())
        sequences = []
        
        for item in temporal_list:
            seq = TemporalSequence.from_dict(item)
            sequences.append(seq)
        
        return sequences
    
    def get_geometry_metadata(self) -> Dict[str, Any]:
        """Get geometry metadata."""
        meta_data = self.container.get_chunk(self.CHUNK_GEOMETRY_META)
        if not meta_data:
            return {}
        
        return json.loads(meta_data.decode())
    
    def validate_geometry_integrity(self) -> bool:
        """Validate geometry data integrity in container."""
        try:
            # Try to load all geometry data
            tokens = self.get_geometry_tokens()
            sequences = self.get_temporal_sequences()
            metadata = self.get_geometry_metadata()
            
            # Basic validation
            if tokens:
                # Verify token count matches metadata
                if metadata.get("token_count", 0) != len(tokens):
                    return False
                
                # Verify all tokens can be properly loaded
                for token in tokens:
                    if not token.uid:
                        return False
            
            if sequences:
                # Verify sequence consistency
                for seq in sequences:
                    if not seq.keyframes:
                        return False
                    if seq.duration_frames <= 0:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def create_geometry_summary(self) -> Dict[str, Any]:
        """Create summary of geometry data in container."""
        tokens = self.get_geometry_tokens()
        sequences = self.get_temporal_sequences()
        metadata = self.get_geometry_metadata()
        
        # Calculate bounds
        bounds = {
            "min_x": float("inf"), "max_x": float("-inf"),
            "min_y": float("inf"), "max_y": float("-inf"),
            "min_z": float("inf"), "max_z": float("-inf"),
        }
        
        for token in tokens:
            bx, by, bz = token.bounds
            bounds["min_x"] = min(bounds["min_x"], -bx/2)
            bounds["max_x"] = max(bounds["max_x"], bx/2)
            bounds["min_y"] = min(bounds["min_y"], -by/2)
            bounds["max_y"] = max(bounds["max_y"], by/2)
            bounds["min_z"] = min(bounds["min_z"], -bz/2)
            bounds["max_z"] = max(bounds["max_z"], bz/2)
        
        return {
            "geometry": {
                "token_count": len(tokens),
                "primitive_count": sum(1 for t in tokens 
                                     if t.token_type.value == "primitive"),
                "transform_count": sum(1 for t in tokens 
                                     if t.token_type.value == "transform"),
                "temporal_count": sum(1 for t in tokens 
                                    if t.token_type.value == "temporal"),
            },
            "animation": {
                "sequence_count": len(sequences),
                "duration_frames": sequences[0].duration_frames if sequences else 0,
                "animated_properties": list(set(s.property_name for s in sequences)),
            },
            "bounds": bounds,
            "metadata": metadata,
            "integrity_check": self.validate_geometry_integrity()
        }


# Factory function
def create_geometry_container(h4mk_container) -> GeometryContainer:
    """Create geometry container from H4MK container."""
    return GeometryContainer(h4mk_container)
