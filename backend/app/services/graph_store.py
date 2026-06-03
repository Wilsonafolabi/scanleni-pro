import networkx as nx
import json
from pathlib import Path
from typing import Dict, Any

GRAPH_PATH = Path(__file__).parent.parent.parent / "data" / "ingredient_graph.json"

class IngredientGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._load_or_init()

    def _load_or_init(self):
        if GRAPH_PATH.exists():
            data = json.loads(GRAPH_PATH.read_text())
            for node, attrs in data.get("nodes", {}).items():
                self.graph.add_node(node, **attrs)
            for u, v, attrs in data.get("edges", []):
                self.graph.add_edge(u, v, **attrs)
        else:
            self._build_default()
            self.save()

    def _build_default(self):
        ingredients = {
            "parabens": {"category": "preservative", "risk": "high", "effects": ["endocrine_disruption", "skin_irritation"]},
            "retinol": {"category": "active", "risk": "moderate", "effects": ["photosensitivity", "anti_aging"]},
            "fragrance": {"category": "additive", "risk": "moderate", "effects": ["allergen", "respiratory_irritation"]},
            "niacinamide": {"category": "active", "risk": "low", "effects": ["barrier_repair", "anti_inflammatory"]},
            "sodium_lauryl_sulfate": {"category": "surfactant", "risk": "moderate", "effects": ["barrier_stripping", "acne_trigger"]},
            "alcohol_denat": {"category": "solvent", "risk": "moderate", "effects": ["drying", "barrier_disruption"]},
            "mineral_oil": {"category": "emollient", "risk": "moderate", "effects": ["comedogenic", "occlusive"]}
        }
        for ing, meta in ingredients.items():
            self.graph.add_node(ing, **meta)
            for effect in meta["effects"]:
                self.graph.add_edge(ing, effect, relation="causes")

    def save(self):
        data = {
            "nodes": {n: dict(self.graph.nodes[n]) for n in self.graph.nodes()},
            "edges": [(u, v, dict(d)) for u, v, d in self.graph.edges(data=True)]
        }
        GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_PATH.write_text(json.dumps(data, indent=2))

    def get_related(self, ingredient: str, depth: int = 2) -> Dict[str, Any]:
        normalized = ingredient.lower().replace(" ", "_")
        if normalized not in self.graph:
            return {}
        sub = nx.ego_graph(self.graph, normalized, radius=depth)
        return {n: dict(sub.nodes[n]) for n in sub.nodes()}

    def query_effects(self, effects: list[str]) -> Dict[str, Any]:
        matches = {}
        for ing in self.graph.nodes():
            ing_effects = self.graph.nodes[ing].get("effects", [])
            if any(e in ing_effects for e in effects):
                matches[ing] = self.graph.nodes[ing]
        return matches

graph_store = IngredientGraph()