import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
from rapidocr_onnxruntime import RapidOCR
from app.models.schemas import TextBlock, BBox
from app.config import settings
import re

class OCRService:
    def __init__(self):
        # Optimized for product labels: angle classification, higher det limit, batch processing
        self.engine = RapidOCR(
            use_angle_cls=True,
            det_limit_side_len=1500,
            rec_batch_num=6,
            print_verbose=False
        )
        self.threshold = settings.OCR_CONFIDENCE_THRESHOLD

    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Product label optimization: sharpen, boost contrast, reduce color noise"""
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Color(img).enhance(0.7)  # Slight desaturation helps text pop
        return img

    def _clean_text(self, text: str) -> str:
        """Fix OCR fragmentation, remove noise, merge broken words"""
        text = re.sub(r'[^a-zA-Z0-9\s,./()-]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Drop single-character noise unless it's a known initial (e.g., "E", "U")
        if len(text) <= 1 and text.upper() not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return ""
        return text

    def extract(self, image_bytes: bytes) -> list[TextBlock]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = self._enhance_image(img)

        if max(img.size) > settings.OCR_MAX_DIM:
            img.thumbnail((settings.OCR_MAX_DIM, settings.OCR_MAX_DIM))

        result, _ = self.engine(np.array(img))
        blocks = []
        if result:
            for box, text, conf in result:
                cleaned = self._clean_text(text)
                if conf >= self.threshold and len(cleaned) > 1:
                    blocks.append(TextBlock(
                        text=cleaned,
                        confidence=float(conf),
                        bbox=BBox(points=box),
                        category=self._classify(cleaned)
                    ))
        return blocks

    def _classify(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["water", "aqua", "glycerin", "oil", "corn", "sugar", "flour"]): return "base"
        if any(k in t for k in ["paraben", "sulfate", "phthalate", "benzoate"]): return "preservative"
        if any(k in t for k in ["fragrance", "parfum", "aroma"]): return "fragrance"
        if any(k in t for k in ["vitamin", "niacinamide", "retinol", "zinc"]): return "active"
        return "other"

ocr_service = OCRService()