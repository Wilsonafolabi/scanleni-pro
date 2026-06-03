import re
from typing import List

def clean_ingredient_text(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s,./()-]', '', text)
    return text.strip()

def parse_ingredients(blocks: list) -> List[str]:
    raw = " ".join([b.text for b in blocks])
    cleaned = clean_ingredient_text(raw)
    ingredients = [i.strip() for i in cleaned.split(',') if len(i.strip()) > 2]
    return ingredients
