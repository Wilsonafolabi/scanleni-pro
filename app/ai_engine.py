from app.schemas import TextBlock, AIAnalysis
from app.rag_engine import rag_engine

def analyze_ingredients(blocks: list[TextBlock]) -> AIAnalysis:
    full_text = " ".join([b.text.lower() for b in blocks])
    retrieved = rag_engine.retrieve(full_text, top_k=3)
    
    found_harms = []
    context_snippets = []
    
    for item in retrieved:
        context_snippets.append(f"{item['ingredient']}: {item['description']}")
        if item.get("risk_level") in ["high", "moderate"]:
            for block in blocks:
                if item["ingredient"].lower() in block.text.lower():
                    block.is_harmful = True
                    block.harm_reason = item["description"]
                    found_harms.append(item["ingredient"])

    if found_harms:
        status = "DANGER" if len(found_harms) > 2 else "WARNING"
        summary = f"Detected {len(found_harms)} flagged ingredients."
        chat = f"Analysis: This product contains {', '.join(found_harms)}. {retrieved[0]['description'] if retrieved else 'Consider cleaner alternatives.'}"
    else:
        status = "SAFE"
        summary = "No flagged ingredients detected."
        chat = "This product appears clean based on current safety data. No major concerns found."

    return AIAnalysis(
        summary=summary,
        safety_status=status,
        chat_response=chat,
        retrieved_context=context_snippets
    )
