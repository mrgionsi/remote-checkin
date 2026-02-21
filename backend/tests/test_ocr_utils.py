"""Unit tests for OCR document validation helpers."""

import numpy as np
from pytesseract import TesseractNotFoundError

from utils.ocr_utils import validate_document


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
            return ("Documento di identita valido", 82.0)
        return ("noise", 10.0)

    monkeypatch.setattr("utils.ocr_utils._extract_with_confidence", fake_extract)
    result = validate_document("doc.jpg")
    assert result["valid"] is True
    assert result["variant"] == "adaptive"
    assert calls["count"] >= 2


def test_validate_document_handles_missing_tesseract(monkeypatch):
    """Should return operational error when OCR engine is unavailable."""
    monkeypatch.setattr(
        "utils.ocr_utils.cv2.imread", lambda _: np.zeros((20, 20, 3), dtype=np.uint8)
    )
    monkeypatch.setattr("utils.ocr_utils._preprocess_variants", lambda _: {"gray": "gray"})
    monkeypatch.setattr(
        "utils.ocr_utils._extract_with_confidence",
        lambda _: (_ for _ in ()).throw(TesseractNotFoundError()),
    )
    result = validate_document("doc.jpg")
    assert result["valid"] is False
    assert "OCR engine not available" in result["error"]
