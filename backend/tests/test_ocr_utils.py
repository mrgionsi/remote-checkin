"""Unit tests for OCR document validation helpers."""

import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError

from utils.ocr_utils import (
    MIN_OCR_CONFIDENCE,
    MIN_TEXT_LENGTH,
    validate_document,
)


def test_validate_document_rejects_unreadable_image(monkeypatch):
    """Should return a clear error when image cannot be loaded."""
    monkeypatch.setattr("utils.ocr_utils.cv2.imread", lambda _: None)
    result = validate_document("missing.jpg")
    assert result["valid"] is False
    assert "Could not load image" in result["error"]


def test_validate_document_returns_best_valid_variant(monkeypatch):
    """Should accept document when at least one variant is valid."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )
    monkeypatch.setattr(
        "utils.ocr_utils._preprocess_variants",
        lambda _: {"gray": "gray", "adaptive": "adaptive", "otsu": "otsu"},
    )

    calls = {"count": 0}

    def fake_extract(variant):
        calls["count"] += 1
        if variant == "adaptive":
            return ("A" * MIN_TEXT_LENGTH, MIN_OCR_CONFIDENCE)
        return ("noise", MIN_OCR_CONFIDENCE - 5.0)

    monkeypatch.setattr("utils.ocr_utils._extract_with_confidence", fake_extract)
    result = validate_document("doc.jpg")
    assert result["valid"] is True
    assert result["variant"] == "adaptive"
    assert calls["count"] == 2


def test_validate_document_handles_missing_tesseract(monkeypatch):
    """Should return operational error when OCR engine is unavailable."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )
    monkeypatch.setattr("utils.ocr_utils._preprocess_variants", lambda _: {"gray": "gray"})
    def raise_tesseract_not_found(_):
        raise TesseractNotFoundError()

    monkeypatch.setattr("utils.ocr_utils._extract_with_confidence", raise_tesseract_not_found)
    result = validate_document("doc.jpg")
    assert result["valid"] is False
    assert "OCR engine not available" in result["error"]


def test_validate_document_handles_preprocess_failure(monkeypatch):
    """Should return preprocess error payload when preprocessing fails."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )

    def raise_bad_image(_):
        raise RuntimeError("bad image")

    monkeypatch.setattr("utils.ocr_utils._preprocess_variants", raise_bad_image)
    result = validate_document("doc.jpg")
    assert result["valid"] is False
    assert "Failed to process image" in result["error"]


def test_validate_document_handles_tesseract_error(monkeypatch):
    """Should return OCR error payload when pytesseract fails."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )
    monkeypatch.setattr("utils.ocr_utils._preprocess_variants", lambda _: {"gray": "gray"})

    def raise_tesseract_error(_):
        raise pytesseract.TesseractError(1, "err")

    monkeypatch.setattr("utils.ocr_utils._extract_with_confidence", raise_tesseract_error)
    result = validate_document("doc.jpg")
    assert result["valid"] is False
    assert "OCR processing error" in result["error"]


def test_validate_document_returns_best_invalid_variant(monkeypatch):
    """Should return best variant details even when all variants are invalid."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )
    monkeypatch.setattr(
        "utils.ocr_utils._preprocess_variants",
        lambda _: {"gray": "gray", "adaptive": "adaptive", "otsu": "otsu"},
    )

    def low_conf_extract(variant):
        if variant == "adaptive":
            return ("text", 8.0)
        if variant == "otsu":
            return ("text", 5.0)
        return ("text", 3.0)

    monkeypatch.setattr("utils.ocr_utils._extract_with_confidence", low_conf_extract)
    result = validate_document("doc.jpg")
    assert result["valid"] is False
    assert result["error"] == "No valid text detected"
    assert result["variant"] == "adaptive"
