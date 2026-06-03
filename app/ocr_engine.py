import io
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
from app.schemas import TextBlock, BBox

class OCREngine:
    def __init__(self):
        self.model = RapidOCR()

    def process_image(self, image_bytes: bytes) -> list[TextBlock]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if max(img.size) > 1500:
            img.thumbnail((1500, 1500))

        result, _ = self.model(img)
        blocks = []
        if result:
            for box, text, conf in result:
                if conf >= 0.4:  # Lowered to capture full ingredient lists
                    blocks.append(TextBlock(
                        text=text.strip(),
                        confidence=float(conf),
                        bbox=BBox(points=box)
                    ))
        return blocks

ocr_engine = OCREngine()
