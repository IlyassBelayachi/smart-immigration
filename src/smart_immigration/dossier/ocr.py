"""Lecture locale des pages PDF sans texte sélectionnable."""
from contextlib import closing
from functools import lru_cache
from pathlib import Path
from threading import Lock

from pypdfium2 import PdfDocument, PdfiumError
from rapidocr_onnxruntime import RapidOCR

_OCR_LOCK = Lock()


@lru_cache(maxsize=1)
def _engine() -> RapidOCR:
    latin_model = Path(__file__).with_name("latin_PP-OCRv3_rec_mobile.onnx")
    return RapidOCR(rec_model_path=str(latin_model), intra_op_num_threads=2, inter_op_num_threads=1)


def read_scanned_pages(content: bytes, page_indexes: list[int]) -> dict[int, list[tuple[str, float]]]:
    recognized = {}
    try:
        # PDFium et le moteur OCR sont utilisés par un seul thread à la fois.
        with _OCR_LOCK, closing(PdfDocument(content)) as pdf:
            for index in page_indexes:
                with closing(pdf[index]) as page:
                    width, height = page.get_size()
                    scale = min(3, 2200 / max(width, height, 1))
                    with closing(page.render(scale=scale)) as bitmap:
                        lines, _ = _engine()(bitmap.to_numpy())
                recognized[index] = [(line, float(score)) for _, line, score in (lines or [])]
    except (PdfiumError, RuntimeError) as error:
        raise ValueError("Impossible de lire les pages scannées de ce PDF.") from error
    return recognized
