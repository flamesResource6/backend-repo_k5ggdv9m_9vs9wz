import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Property, Faq, Conversation, ConversationMessage, Lead, BookingRequest

app = FastAPI(title="AI Receptionist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "AI Receptionist API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:120]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response

# --- Bootstrap endpoints ---
@app.post("/api/property", response_model=dict)
def upsert_property(payload: Property):
    try:
        # For demo: insert a new property document (could be upsert by name in real app)
        inserted_id = create_document("property", payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property", response_model=list)
def get_property_sample():
    try:
        props = get_documents("property", {}, limit=1)
        return props
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- FAQs ---
@app.post("/api/faqs", response_model=dict)
def add_faq(faq: Faq):
    try:
        _id = create_document("faq", faq)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faqs", response_model=list)
def list_faqs():
    try:
        return get_documents("faq", {}, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Conversations ---
class ConversationIn(BaseModel):
    visitor_id: str
    message: str
    lang: Optional[str] = None

@app.post("/api/conversations/start", response_model=dict)
def start_conversation(payload: ConversationIn):
    try:
        conv = Conversation(
            visitor_id=payload.visitor_id,
            messages=[ConversationMessage(role='user', content=payload.message, lang=payload.lang)]
        )
        conv_id = create_document("conversation", conv)
        # Simple heuristic "AI" response. In a real app you'd call an LLM provider here.
        ai_reply = generate_ai_reply(payload.message)
        create_document("conversation", Conversation(
            visitor_id=payload.visitor_id,
            messages=[ConversationMessage(role='assistant', content=ai_reply, lang=payload.lang)],
            status='open'
        ))
        return {"conversation_id": conv_id, "reply": ai_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/message", response_model=dict)
def add_message(conversation_id: str, payload: ConversationIn):
    try:
        # Persist message as separate document for simplicity
        create_document("conversation", Conversation(
            visitor_id=payload.visitor_id,
            messages=[ConversationMessage(role='user', content=payload.message, lang=payload.lang)],
            status='open'
        ))
        ai_reply = generate_ai_reply(payload.message)
        create_document("conversation", Conversation(
            visitor_id=payload.visitor_id,
            messages=[ConversationMessage(role='assistant', content=ai_reply, lang=payload.lang)],
            status='open'
        ))
        return {"reply": ai_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Leads ---
@app.post("/api/leads", response_model=dict)
def create_lead(lead: Lead):
    try:
        _id = create_document("lead", lead)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads", response_model=list)
def list_leads():
    try:
        return get_documents("lead", {}, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Booking Requests ---
@app.post("/api/bookings", response_model=dict)
def request_booking(br: BookingRequest):
    try:
        _id = create_document("bookingrequest", br)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings", response_model=list)
def list_bookings():
    try:
        return get_documents("bookingrequest", {}, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Simple AI reply generator (placeholder without external deps) ---
def generate_ai_reply(message: str) -> str:
    text = message.lower().strip()
    if any(k in text for k in ["check-in", "check in", "arrival"]):
        return "Check-in is at 3:00 PM. Early check-in is subject to availability."
    if any(k in text for k in ["check-out", "check out", "departure"]):
        return "Check-out is at 11:00 AM. Late check-out may be available upon request."
    if any(k in text for k in ["wifi", "wi-fi", "internet"]):
        return "Yes, complimentary high-speed Wi‑Fi is available throughout the property."
    if any(k in text for k in ["parking", "car"]):
        return "Parking is available on-site. Please check with the front desk for rates and availability."
    if any(k in text for k in ["pet", "dog", "cat"]):
        return "We are pet-friendly for select rooms. A cleaning fee may apply."
    if any(k in text for k in ["pool", "gym", "fitness", "spa"]):
        return "Our amenities include fitness center access from 6 AM to 10 PM."
    if any(k in text for k in ["rate", "price", "cost"]):
        return "Standard rates start from $89 per night before taxes and fees."
    return "Thanks for reaching out! How can I assist with your stay, booking, or questions today?"

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
