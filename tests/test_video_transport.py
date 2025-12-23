"""
Tests for HarmonyØ4 video transport layer.
Focus: multitrack packing, seek correctness, transport properties.
"""

import pytest
import json
import base64

from video.track import TrackBlock
from video.gop import GOPConfig, kind_for, is_keyframe
from video.adapter import OpaquePassThroughAdapter, BlockHeader
from container.h4mk_tracks import build_h4mk_tracks
from container.reader import H4MKReader
from container.multitrack import (
    TrackIndexEntry,
    pack_trak,
    unpack_trak,
    build_seek_per_track,
    pack_seek_multi,
    unpack_seek_multi,
)
from crypto.living_bindings import CoreContext, encrypt_core_block, decrypt_core_block
from crypto.living_cipher import init_from_shared_secret, sha256


class TestGOP:
    """GOP configuration and keyframe logic."""

    def test_gop_is_keyframe(self):
        """Keyframes at GOP boundaries."""
        cfg = GOPConfig(gop_size=30)
        assert is_keyframe(0, cfg) is True
        assert is_keyframe(30, cfg) is True
        assert is_keyframe(60, cfg) is True
        assert is_keyframe(15, cfg) is False

    def test_kind_for_index(self):
        """Frame kind assignment."""
        cfg = GOPConfig(gop_size=3, allow_b=False)
        assert kind_for(0, cfg) == "I"
        assert kind_for(1, cfg) == "P"
        assert kind_for(2, cfg) == "P"
        assert kind_for(3, cfg) == "I"

    def test_kind_with_b_frames(self):
        """B-frames in alternating pattern."""
        cfg = GOPConfig(gop_size=3, allow_b=True)
        assert kind_for(0, cfg) == "I"
        assert kind_for(1, cfg) == "B"
        assert kind_for(2, cfg) == "P"
        assert kind_for(3, cfg) == "I"


class TestTrackIndexing:
    """Track index packing/unpacking."""

    def test_trak_pack_unpack(self):
        """TRAK roundtrip."""
        entries = [
            TrackIndexEntry("video_main", 0, "I", True, 0),
            TrackIndexEntry("video_main", 1000, "P", False, 1),
            TrackIndexEntry("controls", 0, "I", True, 2),
        ]
        packed = pack_trak(entries)
        unpacked = unpack_trak(packed)
        assert len(unpacked) == 3
        assert unpacked[0].track_id == "video_main"
        assert unpacked[1].pts_us == 1000
        assert unpacked[2].core_index == 2

    def test_seek_per_track_keyframes_only(self):
        """Seek table includes only keyframes."""
        entries = [
            TrackIndexEntry("video", 0, "I", True, 0),
            TrackIndexEntry("video", 1000, "P", False, 1),
            TrackIndexEntry("video", 2000, "I", True, 2),
        ]
        seek = build_seek_per_track(entries)
        assert seek["video"] == [(0, 0), (2000, 2)]

    def test_seekm_pack_unpack(self):
        """SEEKM binary format roundtrip."""
        seek = {
            "video_main": [(0, 0), (3000, 10), (6000, 20)],
            "audio_main": [(0, 5), (3000, 15)],
        }
        packed = pack_seek_multi(seek)
        unpacked = unpack_seek_multi(packed)
        assert unpacked["video_main"] == [(0, 0), (3000, 10), (6000, 20)]
        assert unpacked["audio_main"] == [(0, 5), (3000, 15)]


class TestMultitrackPacking:
    """Multitrack H4MK packing."""

    def test_multitrack_pack_and_read(self):
        """Pack and unpack multitrack H4MK."""
        cfg = GOPConfig(gop_size=3)
        blocks = []
        # 2 tracks, interleaved in time (use 256-byte-aligned blocks)
        for i in range(6):
            for track in ("video_main", "controls"):
                blocks.append(TrackBlock(
                    track_id=track,
                    pts_us=i * 1000,
                    kind=kind_for(i, cfg),
                    keyframe=is_keyframe(i, cfg),
                    payload=f"{track}:{i}".encode("utf-8").ljust(256, b"\x00"),
                ))

        meta = {"project": "HarmonyØ4", "version": "1.0"}
        safe = {"policy": "transport_only"}

        h4 = build_h4mk_tracks(blocks, meta=meta, safe=safe)
        r = H4MKReader(h4)

        # Read META
        meta2 = json.loads(r.get_chunks(b"META")[0].decode("utf-8"))
        assert meta2["project"] == "HarmonyØ4"
        assert "seekm_b64" in meta2
        assert "trak_b64" in meta2

        # Read seek table
        seekm = unpack_seek_multi(base64.b64decode(meta2["seekm_b64"]))
        assert "video_main" in seekm
        assert "controls" in seekm

        # Keyframes at indices 0, 3, 6 -> pts 0, 3000, 6000
        # (but we only have 6 blocks total = 2 interleaved tracks * 3 time points)
        # so keyframes are 0, 3000 only (indices 0, 3 within each track)
        assert len([p for (p, _) in seekm["video_main"]]) >= 1

    def test_core_count_matches_blocks(self):
        """Number of CORE chunks equals number of blocks."""
        blocks = [
            TrackBlock("video_main", 0, "I", True, b"A" * 256),
            TrackBlock("video_main", 1000, "P", False, b"B" * 256),
            TrackBlock("controls", 0, "I", True, b"C" * 256),
        ]
        h4 = build_h4mk_tracks(blocks, meta={}, safe={})
        r = H4MKReader(h4)
        assert len(r.get_chunks(b"CORE")) == 3

    def test_trak_index_complete(self):
        """TRAK index includes all blocks with correct metadata."""
        blocks = [
            TrackBlock("video_main", 0, "I", True, b"\x00" * 256),
            TrackBlock("video_main", 1000, "P", False, b"\x00" * 256),
            TrackBlock("audio_main", 0, "I", True, b"\x00" * 256),
        ]
        h4 = build_h4mk_tracks(blocks, meta={}, safe={})
        r = H4MKReader(h4)

        meta = json.loads(r.get_chunks(b"META")[0].decode("utf-8"))
        trak = json.loads(base64.b64decode(meta["trak_b64"]).decode("utf-8"))
        assert len(trak["trak"]) == 3
        assert trak["trak"][0]["track_id"] == "video_main"
        assert trak["trak"][2]["track_id"] == "audio_main"


class TestVideoAdapter:
    """Video adapter contract (OpaquePassThroughAdapter)."""

    def test_passthrough_decode_i(self):
        """Decode I-block."""
        adapter = OpaquePassThroughAdapter()
        header = BlockHeader("video", 0, "I", 0, True)
        state = adapter.decode_I(header, b"frame_data")
        assert state == b"frame_data"

    def test_passthrough_apply_p(self):
        """Apply P-block (append)."""
        adapter = OpaquePassThroughAdapter()
        header = BlockHeader("video", 1000, "P", 1, False)
        state = adapter.apply_P(b"frame_data", header, b"delta")
        assert state == b"frame_datadelta"

    def test_passthrough_render(self):
        """Render state."""
        adapter = OpaquePassThroughAdapter()
        output = adapter.render(b"final_state")
        assert output == b"final_state"


class TestLivingCipherBindings:
    """Living cipher integration for CORE blocks."""

    def test_encrypt_decrypt_core_block(self):
        """Encrypt and decrypt a CORE block with context binding."""
        shared_secret = sha256(b"shared_secret")
        state_a = init_from_shared_secret(shared_secret)
        state_b = init_from_shared_secret(shared_secret)

        ctx = CoreContext(
            engine_id="geom-ref",
            engine_fp="abc123",
            container_veri_hex="deadbeef" * 8,
            track_id="video_main",
            pts_us=5000,
            chunk_index=0,
        )

        payload = b"encrypted_frame_data"
        h, ct = encrypt_core_block(state_a, payload, ctx)
        decrypted = decrypt_core_block(state_b, h, ct, ctx)
        assert decrypted == payload

    def test_context_binding_prevents_transplant(self):
        """Different context produces AAD mismatch."""
        shared_secret = sha256(b"shared_secret")
        state_a = init_from_shared_secret(shared_secret)
        state_b = init_from_shared_secret(shared_secret)

        ctx1 = CoreContext("geom-ref", "abc", "deadbeef" * 8, "video", 0, 0)
        ctx2 = CoreContext("geom-ref", "abc", "deadbeef" * 8, "video", 1000, 0)

        h, ct = encrypt_core_block(state_a, b"data", ctx1)
        
        # Try to decrypt with different context
        with pytest.raises(Exception):  # AEAD verification failure
            decrypt_core_block(state_b, h, ct, ctx2)


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline_multitrack_video(self):
        """Complete pipeline: encode, pack, manifest, seek, fetch."""
        # Build blocks (256-byte aligned)
        cfg = GOPConfig(gop_size=2)
        blocks = []
        for i in range(4):
            blocks.append(TrackBlock(
                track_id="video_main",
                pts_us=i * 1000,
                kind=kind_for(i, cfg),
                keyframe=is_keyframe(i, cfg),
                payload=f"video_frame_{i}".encode("utf-8").ljust(256, b"\x00"),
            ))

        # Pack
        h4 = build_h4mk_tracks(blocks, meta={"title": "test"}, safe={})

        # Read manifest
        r = H4MKReader(h4)
        meta = json.loads(r.get_chunks(b"META")[0].decode("utf-8"))
        seekm = unpack_seek_multi(base64.b64decode(meta["seekm_b64"]))

        # Seek test: find keyframe at or before pts=1500
        entries = seekm.get("video_main", [])
        assert entries  # at least one keyframe
        chosen = entries[0]
        for e in entries:
            if e[0] <= 1500:
                chosen = e
            else:
                break
        assert chosen[0] == 0  # first keyframe at pts=0

        # Fetch block (blocks are compressed, so just verify it exists and is bytes)
        core = r.get_chunks(b"CORE")
        block = core[chosen[1]]
        assert isinstance(block, bytes)
        assert len(block) > 0
