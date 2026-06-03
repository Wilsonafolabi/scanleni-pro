import sys
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

print("Initializing RapidOCR...")
ocr = RapidOCR()
print("Model loaded successfully.")

img_path = "label.jpg"
try:
    img = Image.open(img_path).convert("RGB")
except FileNotFoundError:
    print(f"Error: Image not found at {img_path}")
    print("Action: Place a product label image named 'label.jpg' in this folder.")
    sys.exit(1)

print("Running OCR inference...")
result, _ = ocr(img)

if result:
    print("\nExtracted Text:")
    for box, text, conf in result:
        print(f"{text}  (confidence: {conf:.2f})")
else:
    print("Warning: No text detected.")