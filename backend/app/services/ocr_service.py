import logging
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR
from app.models.schemas import TextBlock, BBox

logger = logging.getLogger(__name__)

class OcrService:
    def __init__(self):
        logger.info("Initializing RapidOCR engine...")
        self.engine = RapidOCR()
        logger.info("RapidOCR initialized successfully.")

    def extract(self, image_bytes: bytes) -> list[TextBlock]:
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            img_np = np.array(image)
            
            # RapidOCR returns: [[bbox, text, confidence], ...]
            results, _ = self.engine(img_np)
            
            if not results:
                return []
            
            ocr_data = []
            for bbox, text, confidence in results:
                ocr_data.append(
                    TextBlock(
                        text=text.strip(),
                        confidence=float(confidence),
                        bbox=BBox(points=bbox),
                        is_harmful=False,
                        harm_reason=None,
                        category=None
                    )
                )
            return ocr_data
        except Exception as e:
            logger.error("OCR extraction failed: %s", str(e))
            return []

ocr_service = OcrService()