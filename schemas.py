"""
Database Schemas for AI Receptionist (Hospitality)

Each Pydantic model maps to a MongoDB collection where the collection name is the lowercase
of the class name (e.g., Property -> "property").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import date

class Property(BaseModel):
    name: str = Field(..., description="Property name")
    description: Optional[str] = Field(None, description="Short description of the hotel/motel")
    address: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    website: Optional[str] = Field(None)
    check_in_time: Optional[str] = Field("3:00 PM")
    check_out_time: Optional[str] = Field("11:00 AM")
    amenities: List[str] = Field(default_factory=lambda: ["Free Wi‑Fi", "Parking", "Breakfast available"]) 
    currency: str = Field("USD")
    timezone: Optional[str] = Field(None)
    rooms_total: int = Field(20, ge=0)
    rooms_available: int = Field(20, ge=0)
    min_rate: Optional[float] = Field(79.0, ge=0)
    max_rate: Optional[float] = Field(249.0, ge=0)

class Faq(BaseModel):
    question: str
    answer: str
    tags: List[str] = Field(default_factory=list)

class ConversationMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    lang: Optional[str] = Field(None, description="Language code if detected")

class Conversation(BaseModel):
    visitor_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    status: Literal['open','closed'] = 'open'
    source: Literal['web','kiosk','sms','whatsapp','phone'] = 'web'

class Lead(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Literal['new','contacted','qualified','booked','closed'] = 'new'

class BookingRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    check_in: date
    check_out: date
    adults: int = 2
    children: int = 0
    special_requests: Optional[str] = None
    estimated_rate: Optional[float] = None
    currency: str = 'USD'
    conversation_id: Optional[str] = None

