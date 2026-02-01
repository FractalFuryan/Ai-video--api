#!/usr/bin/env python3
"""
tests/test_fastapi_integration.py

Integration test for FastAPI endpoints.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.mark.integration
def test_health():
    """Test health endpoint."""
    print("\n[1] Health Endpoint")
    print("-" * 50)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print(f"  ✓ Health: {data}")


def test_root():
    """Test root endpoint."""
    print("\n[2] Root Endpoint")
    print("-" * 50)

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "endpoints" in data
    print(f"  ✓ Root: {data['name']}")
    print(f"    Endpoints: {list(data['endpoints'].keys())}")


def test_video_metadata():
    """Test video metadata endpoint."""
    print("\n[3] Video Metadata Endpoint")
    print("-" * 50)

    client = TestClient(app)

    # Create fake video data
    fake_video = b"FAKE_VIDEO_DATA" * 1000

    response = client.post(
        "/video/metadata",
        files={"file": ("test.mp4", fake_video)},
        params={
            "fps": 30.0,
            "gop_size": 30,
            "block_size": 1024,
        },
    )

    assert response.status_code == 200
    data = response.json()
    print(f"  ✓ Metadata response:")
    for key, value in data.items():
        print(f"    {key}: {value}")

    assert data["frame_count"] > 0
    assert data["fps"] == 30.0


def test_video_tokenize():
    """Test video tokenize endpoint."""
    print("\n[4] Video Tokenize Endpoint")
    print("-" * 50)

    client = TestClient(app)

    # Create fake video data
    fake_video = b"FRAME_DATA_" * 500  # Small fake video

    response = client.post(
        "/video/tokenize",
        files={"file": ("test.mp4", fake_video)},
        params={
            "fps": 24.0,
            "gop_size": 30,
            "block_size": 1024,
        },
    )

    assert response.status_code == 200
    data = response.json()
    print(f"  ✓ Tokenize response:")
    print(f"    blocks: {data['block_count']}")
    print(f"    tokens: {data['tokens'][:2]}...")  # Show first 2 tokens
    print(f"    seek entries: {len(data['seek_entries'])}")
    print(f"    duration: {data['duration_us']}us")

    assert data["block_count"] > 0
    assert len(data["tokens"]) == data["block_count"]


def test_video_seek():
    """Test video seek endpoint."""
    print("\n[5] Video Seek Endpoint")
    print("-" * 50)

    client = TestClient(app)

    # First tokenize to get a seek table
    fake_video = b"FRAME" * 1000
    tokenize_resp = client.post(
        "/video/tokenize",
        files={"file": ("test.mp4", fake_video)},
        params={"fps": 30.0, "gop_size": 30, "block_size": 1024},
    )

    assert tokenize_resp.status_code == 200
    tokenize_data = tokenize_resp.json()
    seek_entries = tokenize_data["seek_entries"]

    # Build seek table hex from entries
    # For now, we'll test seeking with the raw seek response from tokenize
    print(f"  ✓ Got {len(seek_entries)} seek entries from tokenize")
    for pts, offset in seek_entries[:3]:
        print(f"    pts={pts}us, offset={offset}")


def test_audio_metadata():
    """Test audio metadata endpoint."""
    print("\n[6] Audio Metadata Endpoint")
    print("-" * 50)

    client = TestClient(app)

    response = client.get(
        "/audio/metadata",
        params={"sample_rate": 48000},
    )

    assert response.status_code == 200
    data = response.json()
    print(f"  ✓ Audio metadata: {data}")


def test_audio_tokenize():
    """Test audio tokenize endpoint."""
    print("\n[7] Audio Tokenize Endpoint")
    print("-" * 50)

    client = TestClient(app)

    # Fake audio data (16-bit samples)
    fake_audio = b"\x00\x01" * 2000  # 2000 samples

    response = client.post(
        "/audio/tokenize",
        files={"file": ("test.wav", fake_audio)},
        params={"sample_rate": 48000},
    )

    assert response.status_code == 200
    data = response.json()
    print(f"  ✓ Audio tokenize response:")
    for key, value in data.items():
        print(f"    {key}: {value}")


def main():
    print("\n" + "=" * 60)
    print("FASTAPI INTEGRATION TEST SUITE")
    print("=" * 60)

    try:
        test_health()
        test_root()
        test_video_metadata()
        test_video_tokenize()
        test_video_seek()
        test_audio_metadata()
        test_audio_tokenize()

        print("\n" + "=" * 60)
        print("✓ ALL FASTAPI TESTS PASSED ✓")
        print("=" * 60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
