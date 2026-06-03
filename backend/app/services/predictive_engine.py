import time
import json
from collections import defaultdict
from typing import Dict, List, Any
from redis import Redis
from app.config import settings

# Fallback to in-memory dict if Redis is unavailable (dev mode)
redis = Redis.from_url(settings.REDIS_URL, decode_responses=True) if hasattr(settings, "REDIS_URL") else None
in_memory_store: Dict[str, List[Dict]] = defaultdict(list)
in_memory_exposures: Dict[str, Dict] = defaultdict(lambda: defaultdict(int))

def track_exposure(user_id: str, ocr_data: list):
    now = int(time.time())
    flagged = [b.text.lower().replace(" ", "_") for b in ocr_data if b.is_harmful]
    
    if redis:
        key = f"user:{user_id}:scans"
        redis.rpush(key, json.dumps({"ts": now, "flagged": len(flagged)}))
        redis.expire(key, 60*60*24*90)
        for ing in flagged:
            exp_key = f"user:{user_id}:exposure:{ing}"
            redis.hincrby(exp_key, "count", 1)
            redis.hset(exp_key, "last_seen", now)
    else:
        in_memory_store[user_id].append({"ts": now, "flagged": len(flagged)})
        if len(in_memory_store[user_id]) > 100:
            in_memory_store[user_id] = in_memory_store[user_id][-100:]
        for ing in flagged:
            in_memory_exposures[user_id][ing] += 1

def get_user_trends(user_id: str) -> Dict[str, Any]:
    scans = []
    exposures = {}
    
    if redis:
        scan_key = f"user:{user_id}:scans"
        scans_raw = redis.lrange(scan_key, 0, 29)
        scans = [json.loads(s) for s in scans_raw]
        exp_keys = redis.keys(f"user:{user_id}:exposure:*")
        for key in exp_keys:
            name = key.split(":")[-1]
            count = int(redis.hget(key, "count") or 0)
            if count > 0:
                exposures[name] = count
    else:
        scans = in_memory_store.get(user_id, [])
        exposures = dict(in_memory_exposures.get(user_id, {}))

    if not scans:
        return {"avg_flagged": 0, "trend": "stable", "top_exposures": [], "insight": "Scan more products to build your health baseline."}

    flagged_counts = [s["flagged"] for s in scans]
    avg = sum(flagged_counts) / len(flagged_counts)
    recent = flagged_counts[-5:]
    older = flagged_counts[:5] if len(flagged_counts) > 5 else []
    trend = "improving" if len(recent) > 0 and len(older) > 0 and sum(recent) < sum(older) else "stable"

    top_exp = sorted(exposures.items(), key=lambda x: x[1], reverse=True)[:3]
    insight = f"Average flagged: {avg:.1f}/scan. "
    if trend == "improving":
        insight += "Your choices are getting cleaner."
    elif top_exp:
        insight += f"Frequent exposure: {', '.join(t[0].replace('_', ' ') for t in top_exp)}."

    return {
        "avg_flagged": round(avg, 1),
        "trend": trend,
        "top_exposures": [{"ingredient": k.replace('_', ' '), "count": v} for k, v in top_exp],
        "insight": insight,
        "scan_count": len(scans)
    }