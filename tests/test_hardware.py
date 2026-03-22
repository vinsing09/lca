"""Tests for lca.runtime.hardware — hardware detection and model recommendation."""
from unittest.mock import MagicMock, patch

import pytest

from lca.runtime.hardware import (
    MODEL_TIERS,
    HardwareProfile,
    _recommend,
    detect_hardware,
)


# ---------------------------------------------------------------------------
# Basic structural tests (real hardware)
# ---------------------------------------------------------------------------

def test_detect_hardware_returns_profile():
    assert isinstance(detect_hardware(), HardwareProfile)


def test_recommended_model_is_known_tier():
    profile = detect_hardware()
    assert profile.recommended_model in MODEL_TIERS.values()


def test_recommendation_reason_nonempty():
    assert detect_hardware().recommendation_reason != ""


def test_ram_gb_positive():
    assert detect_hardware().ram_gb > 0


def test_cpu_cores_positive():
    assert detect_hardware().cpu_cores > 0


def test_not_both_macos_and_linux():
    p = detect_hardware()
    assert not (p.is_macos and p.is_linux)


# ---------------------------------------------------------------------------
# Helpers for mocking psutil + platform
# ---------------------------------------------------------------------------

def _make_mem(gb: float):
    m = MagicMock()
    m.total = int(gb * 1024 ** 3)
    return m


def _profile(ram_gb: float, is_apple_silicon: bool) -> HardwareProfile:
    """Produce a HardwareProfile with mocked RAM and architecture."""
    machine = "arm64" if is_apple_silicon else "x86_64"
    plat = "darwin" if is_apple_silicon else "linux"
    with patch("psutil.virtual_memory", return_value=_make_mem(ram_gb)), \
         patch("psutil.cpu_count", return_value=8), \
         patch("sys.platform", plat), \
         patch("platform.machine", return_value=machine):
        return detect_hardware()


# ---------------------------------------------------------------------------
# RAM tier tests — Apple Silicon
# ---------------------------------------------------------------------------

class TestAppleSiliconTiers:
    def test_4gb_apple_silicon_is_small(self):
        p = _profile(4, is_apple_silicon=True)
        assert p.recommended_model == MODEL_TIERS["small"]

    def test_8gb_apple_silicon_is_large(self):
        p = _profile(8, is_apple_silicon=True)
        assert p.recommended_model == MODEL_TIERS["large"]

    def test_16gb_apple_silicon_is_large(self):
        p = _profile(16, is_apple_silicon=True)
        assert p.recommended_model == MODEL_TIERS["large"]

    def test_32gb_apple_silicon_is_xlarge(self):
        p = _profile(32, is_apple_silicon=True)
        assert p.recommended_model == MODEL_TIERS["xlarge"]

    def test_8gb_apple_silicon_is_not_medium(self):
        """Apple Silicon 8GB → 7B (large), not 3B (medium)."""
        p = _profile(8, is_apple_silicon=True)
        assert p.recommended_model != MODEL_TIERS["medium"]


# ---------------------------------------------------------------------------
# RAM tier tests — Intel / Linux
# ---------------------------------------------------------------------------

class TestIntelLinuxTiers:
    def test_4gb_is_small(self):
        p = _profile(4, is_apple_silicon=False)
        assert p.recommended_model == MODEL_TIERS["small"]

    def test_8gb_is_medium(self):
        """Intel/Linux 8GB → 3B (medium), not 7B (large)."""
        p = _profile(8, is_apple_silicon=False)
        assert p.recommended_model == MODEL_TIERS["medium"]

    def test_12gb_is_medium(self):
        p = _profile(12, is_apple_silicon=False)
        assert p.recommended_model == MODEL_TIERS["medium"]

    def test_16gb_is_large(self):
        p = _profile(16, is_apple_silicon=False)
        assert p.recommended_model == MODEL_TIERS["large"]

    def test_32gb_is_xlarge(self):
        p = _profile(32, is_apple_silicon=False)
        assert p.recommended_model == MODEL_TIERS["xlarge"]

    def test_8gb_intel_is_not_large(self):
        """Intel 8GB should be medium (3B), not large (7B)."""
        p = _profile(8, is_apple_silicon=False)
        assert p.recommended_model != MODEL_TIERS["large"]


# ---------------------------------------------------------------------------
# _recommend unit tests (pure function, no mocking needed)
# ---------------------------------------------------------------------------

class TestRecommendPure:
    def test_apple_silicon_boundary_at_8(self):
        m7, _ = _recommend(8.0, is_apple_silicon=True)
        m_under, _ = _recommend(7.9, is_apple_silicon=True)
        assert m7 == MODEL_TIERS["large"]
        assert m_under == MODEL_TIERS["small"]

    def test_intel_boundary_at_8(self):
        m8, _ = _recommend(8.0, is_apple_silicon=False)
        m_under, _ = _recommend(7.9, is_apple_silicon=False)
        assert m8 == MODEL_TIERS["medium"]
        assert m_under == MODEL_TIERS["small"]
