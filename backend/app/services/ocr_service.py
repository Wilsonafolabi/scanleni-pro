import logging
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
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
            # 1. Load image and convert to grayscale to remove color noise/glare
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            
            # 2. Boost contrast by 40% to make text pop against the background
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.4)
            
            # 3. Apply slight sharpening to counteract motion blur
            image = image.filter(ImageFilter.SHARPEN)
            
            # 4. RapidOCR expects RGB, so convert back for the engine
            img_np = np.array(image.convert('RGB'))
            
            # 5. Run OCR
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