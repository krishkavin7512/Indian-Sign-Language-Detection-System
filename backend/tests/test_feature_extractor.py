import pytest
import numpy as np
from app.services.feature_extractor import FeatureExtractor


@pytest.fixture(scope="module")
def extractor():
    fe = FeatureExtractor()
    yield fe
    fe.close()


def test_extract_landmarks_blank_frame(extractor):
    """Blank frame should return zeros for all landmarks."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = extractor.extract_landmarks(frame)
    assert result["combined"].shape == (258,)
    assert result["landmarks_detected"] is False
    assert np.all(result["left_hand"] == 0)
    assert np.all(result["right_hand"] == 0)


def test_normalize_landmarks_zeros(extractor):
    """Zero array should be returned unchanged."""
    zeros = np.zeros(63)
    result = extractor.normalize_landmarks(zeros)
    assert np.all(result == 0)


def test_normalize_landmarks_nonzero(extractor):
    """Non-zero array should be normalized (mean≈0, std≈1 for non-zero elements)."""
    arr = np.random.rand(63)
    result = extractor.normalize_landmarks(arr)
    assert result.shape == arr.shape
    assert not np.all(result == arr)


def test_combined_shape(extractor):
    """Combined features must be exactly 258 dimensions."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = extractor.extract_landmarks(frame)
    assert result["combined"].shape == (258,)
