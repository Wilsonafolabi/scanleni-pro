import json, os, faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "ingredients.json"
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")

def load_knowledge_base():
    if not KB_PATH.exists():
        return [], []
    with open(KB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    texts = [item["ingredient"] + ": " + item["description"] for item in data]
    return data, texts

def build_index(texts):
    if not texts:
        return None, None
    embeddings = EMBEDDER.encode(texts, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings

class RAGEngine:
    def __init__(self):
        self.data, self.texts = load_knowledge_base()
        self.index, self.embeddings = build_index(self.texts)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.index or len(self.texts) == 0:
            return []
        q_emb = EMBEDDER.encode([query], convert_to_numpy=True)
        D, I = self.index.search(q_emb, top_k)
        results = []
        for idx in I[0]:
            if idx < len(self.data):
                results.append(self.data[idx])
        return results

rag_engine = RAGEngine()
