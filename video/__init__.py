"""
HarmonyØ4 Video Transport Layer

Transport-only, codec/pixel-agnostic video multitrack support.
No identity semantics. No synthesis. Pure data flow.
"""

from video.adapter import VideoAdapter, BlockHeader, OpaquePassThroughAdapter
from video.controls import CameraPath, MotionCurve, VisualControlFrame, encode_controls, decode_controls
from video.gop import GOPConfig, is_keyframe, kind_for
from video.track import Track, TrackBlock

__all__ = [
    "VideoAdapter",
    "BlockHeader",
    "OpaquePassThroughAdapter",
    "CameraPath",
    "MotionCurve",
    "VisualControlFrame",
    "encode_controls",
    "decode_controls",
    "GOPConfig",
    "is_keyframe",
    "kind_for",
    "Track",
    "TrackBlock",
]
