from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: int
    created_at: datetime
    # Slugs of portals that returned a structured error during this response
    # (e.g. ["uslugi", "crm"]).  Empty list = everything worked fine.
    portal_errors: list[str] = []
    # Katastar parcel geometry for mini-map rendering in the frontend.
    # Present only when a katastar__search_property tool was called and
    # returned valid geometry.
    # Shape: { "centroid": [lat, lon], "polygon": [[lat, lon], ...] }
    geometry: dict | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class SessionDetailOut(SessionOut):
    messages: list[MessageOut] = []
