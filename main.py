import os, json
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
# backend.api.calendy_integration
from backend.api.calendy_integration import router as calendly_router
from backend.api.chat import router as chat_router
from backend.rag.vector_store import ensure_collection, upsert_faq

app = FastAPI(title="Medical Scheduling Agent")

# Routers
app.include_router(calendly_router)
app.include_router(chat_router)

@app.on_event("startup")
def _startup():
    # Prepare Qdrant with clinic FAQ (if available)
    try:
        ensure_collection()
        faq_path = os.path.join("data", "clinic_info.json")
        if os.path.exists(faq_path):
            with open(faq_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Expecting a structure like:
            # [{"text":"Parking is available ...", "source":"policies.md"}, ...]
            # If your file is different (e.g., dict), adapt below quickly:
            items = []
            if isinstance(raw, dict):
                # flatten dict to simple records
                for k, v in raw.items():
                    if isinstance(v, str):
                        items.append({"text": v, "source": k})
                    elif isinstance(v, list):
                        for s in v:
                            items.append({"text": s, "source": k})
            elif isinstance(raw, list):
                items = raw
            else:
                items = [{"text": str(raw), "source": "clinic_info"}]

            upsert_faq(items)
    except Exception as e:
        # Non-fatal; scheduling API must remain usable even without FAQ
        print("Qdrant ingest warning:", e)
