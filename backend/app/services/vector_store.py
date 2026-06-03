import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index = None
        self.documents = []
        self.metadata = []
        self._load_default_kb()

    def _load_default_kb(self):
        kb_data = [
            {"text": "sweetcorn, corn, maize: whole grain, generally safe, high in fiber. May cause bloating in sensitive individuals.", "category": "food", "risk": "low"},
            {"text": "cofn, corn flour, maize flour: refined corn starch, safe, commonly used as thickener. Low nutritional value.", "category": "food", "risk": "low"},
            {"text": "sugar, sucrose, cane sugar: high glycemic index, linked to metabolic issues, dental decay. Limit intake.", "category": "sweetener", "risk": "moderate"},
            {"text": "high fructose corn syrup, hfcs: ultra-processed sweetener, strongly linked to insulin resistance and fatty liver.", "category": "sweetener", "risk": "high"},
            {"text": "parabens, methylparaben, propylparaben: preservatives, potential endocrine disruptors, avoid in pregnancy/skincare.", "category": "preservative", "risk": "high"},
            {"text": "sodium lauryl sulfate, sls, sodium laureth sulfate, sles: harsh surfactants, strip skin barrier, cause irritation.", "category": "surfactant", "risk": "moderate"},
            {"text": "fragrance, parfum, aroma: umbrella term for hidden chemicals, common allergen, avoid for sensitive skin/asthma.", "category": "fragrance", "risk": "moderate"},
            {"text": "retinol, retinyl palmitate, vitamin a: anti-aging active, increases sun sensitivity, strictly avoid during pregnancy.", "category": "active", "risk": "moderate"},
            {"text": "niacinamide, vitamin b3: barrier repair, anti-inflammatory, safe for acne, rosacea, and pregnancy.", "category": "active", "risk": "low"},
            {"text": "titanium dioxide, zinc oxide: mineral UV filters, non-nano forms are safe, reef-friendly, low irritation.", "category": "uv_filter", "risk": "low"},
            {"text": "phenoxyethanol: preservative, safe under 1%, can cause contact dermatitis in high concentrations.", "category": "preservative", "risk": "low"},
            {"text": "mineral oil, paraffinum liquidum: occlusive, non-comedogenic but traps debris, avoid for acne-prone skin.", "category": "emollient", "risk": "moderate"},
            {"text": "alcohol denat, sd alcohol: drying solvent, disrupts skin barrier, causes redness, avoid in leave-on skincare.", "category": "solvent", "risk": "moderate"},
            {"text": "red 40, yellow 5, artificial colors: synthetic dyes, linked to hyperactivity in children, potential allergens.", "category": "additive", "risk": "high"},
            {"text": "sodium benzoate, potassium sorbate: common preservatives, safe alone but can form benzene with vitamin C in acidic drinks.", "category": "preservative", "risk": "moderate"},
            {"text": "msg, monosodium glutamate: flavor enhancer, safe for most, may trigger headaches/flushing in sensitive users.", "category": "additive", "risk": "low"},
            {"text": "xanthan gum, guar gum: natural thickeners, fermented, generally safe, may cause mild digestive upset.", "category": "thickener", "risk": "low"},
            {"text": "citric acid, ascorbic acid: natural preservatives, pH adjusters, safe, antioxidant properties.", "category": "active", "risk": "low"}
        ]
        self.documents = [item["text"] for item in kb_data]
        self.metadata = kb_data
        if self.documents:
            embeddings = self.embedder.encode(self.documents, convert_to_numpy=True)
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(embeddings)
            logger.info("Vector store initialized with %d documents", len(self.documents))

    def search(self, query: str, top_k: int = 4) -> List[Tuple[str, float, dict]]:
        if not self.index or len(self.documents) == 0:
            return []
        try:
            q_emb = self.embedder.encode([query], convert_to_numpy=True)
            D, I = self.index.search(q_emb, top_k)
            results = []
            for idx, dist in zip(I[0], D[0]):
                if idx < len(self.documents):
                    results.append((self.documents[idx], float(dist), self.metadata[idx]))
            return results
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            return []

vector_store = VectorStore()