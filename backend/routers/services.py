import json
import secrets
from typing import Optional

import requests as _requests
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.user import User

# In-memory store: token -> uslugi ASP.NET session cookie
_uslugi_sessions: dict[str, str] = {}

USLUGI_BASE = "https://uslugi.gov.mk"

router = APIRouter()

INSTITUTIONS = [
    {
        "slug": "uslugi",
        "name": "uslugi.gov.mk",
        "description": "Главен портал за административни постапки — пасоши, лични карти, возачки дозволи и повеќе.",
        "url": "https://uslugi.gov.mk",
    },
    {
        "slug": "mojtermin",
        "name": "Мој Термин",
        "description": "Систем за закажување медицински прегледи — пронајдете лекари, проверете слободни термини и закажете посета.",
        "url": "https://mojtermin.mk",
    },
    {
        "slug": "crm",
        "name": "Централен регистар",
        "description": "Централен регистар на Северна Македонија — регистрација на компании и деловни услуги.",
        "url": "https://crm.com.mk",
    },
    {
        "slug": "mon",
        "name": "Министерство за образование",
        "description": "Портал за образовни услуги — пријавување документи, барања и услуги за ученици и студенти.",
        "url": "https://e-uslugi.mon.gov.mk",
    },
    {
        "slug": "agencijaZaVrabotuvanje",
        "name": "Агенција за вработување",
        "description": "Агенција за вработување на Република Северна Македонија — огласи за работа, биро за невработени и активни мерки за вработување.",
        "url": "https://av.gov.mk",
    },
    {
        "slug": "katastar",
        "name": "Катастар",
        "description": "Агенција за катастар на недвижности — имотен лист, катастарски планови и услуги поврзани со недвижен имот.",
        "url": "https://katastar.gov.mk",
    },
]


def _disabled_set(user: User) -> set[str]:
    raw = user.disabled_institutions or ""
    return {s.strip() for s in raw.split(",") if s.strip()}


def _save_disabled(user: User, disabled: set[str], db: Session) -> None:
    user.disabled_institutions = ",".join(sorted(disabled))
    db.commit()
    db.refresh(user)


@router.get("/institutions")
def list_institutions(current_user: User = Depends(get_current_user)):
    disabled = _disabled_set(current_user)
    return [
        {**inst, "connected": inst["slug"] not in disabled}
        for inst in INSTITUTIONS
    ]


@router.post("/institutions/{slug}/disconnect", status_code=200)
def disconnect_institution(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not any(i["slug"] == slug for i in INSTITUTIONS):
        raise HTTPException(status_code=404, detail="Institution not found")
    disabled = _disabled_set(current_user)
    disabled.add(slug)
    _save_disabled(current_user, disabled, db)
    return {"slug": slug, "connected": False}


class MojterminContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str


@router.post("/mojtermin/contact", status_code=200)
def mojtermin_contact(
    body: MojterminContactRequest,
    _: User = Depends(get_current_user),
):
    try:
        resp = _requests.post(
            "https://mojtermin.mk/api/pp/contact_message",
            json={"name": body.name, "email": body.email, "message": body.message, "recaptchaResponse": ""},
            headers={"Content-Type": "application/json", "Origin": "https://mojtermin.mk"},
            timeout=10,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="Failed to send message to mojtermin.mk")
        return {"success": True}
    except _requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not reach mojtermin.mk: {e}")


CRM_API = "https://www.crm.com.mk/CRMPublicPortalApi/api/"
CRM_TOPICS = {1: "Пофалби", 2: "Поплаки", 3: "Прашања"}


class CrmContactRequest(BaseModel):
    name: str
    email: EmailStr
    topic: int
    subject: str
    message: str


@router.post("/crm/contact", status_code=200)
def crm_contact(
    body: CrmContactRequest,
    _: User = Depends(get_current_user),
):
    topic_txt = CRM_TOPICS.get(body.topic, "")
    data = {
        "name": body.name,
        "email": body.email,
        "topic": str(body.topic),
        "subject": body.subject,
        "message": body.message,
        "attachmentTxt": "",
        "topicTxt": topic_txt,
    }
    try:
        resp = _requests.post(
            CRM_API + "contact/message",
            data=data,
            headers={"recaptcha": "", "captchaV2Valid": "0"},
            timeout=10,
        )
        if resp.status_code == 412:
            raise HTTPException(status_code=412, detail="captcha_required")
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="Failed to send message to crm.com.mk")
        return {"success": True}
    except _requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not reach crm.com.mk: {e}")


@router.get("/uslugi/captcha")
def uslugi_captcha(_: User = Depends(get_current_user)):
    """Fetch a fresh CAPTCHA image from uslugi.gov.mk and return it with a session token."""
    try:
        resp = _requests.get(
            f"{USLUGI_BASE}/captcha?key=ticketSubmit_sess",
            headers={"Referer": USLUGI_BASE},
            timeout=10,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="Could not fetch captcha")

        # Extract ASP.NET session cookie
        session_cookie = resp.cookies.get("ASP.NET_SessionId", "")

        # Generate a short-lived token to link this session to the form submission
        token = secrets.token_urlsafe(16)
        _uslugi_sessions[token] = session_cookie

        return Response(
            content=resp.content,
            media_type="image/jpeg",
            headers={"X-Captcha-Token": token},
        )
    except _requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not reach uslugi.gov.mk: {e}")


class UslugiContactRequest(BaseModel):
    captcha_token: str
    captcha_value: str
    ticket_type_key: int
    ticket_type_is_subtype: bool
    ticket_title: str
    ticket_body: str
    user_email: Optional[str] = None


@router.post("/uslugi/contact", status_code=200)
def uslugi_contact(
    body: UslugiContactRequest,
    _: User = Depends(get_current_user),
):
    session_cookie = _uslugi_sessions.pop(body.captcha_token, None)
    if session_cookie is None:
        raise HTTPException(status_code=400, detail="Invalid or expired captcha session")

    model = {
        "SelectedTypeOrSubtype": {
            "Key": body.ticket_type_key,
            "IsSubtype": body.ticket_type_is_subtype,
        },
        "TicketTitle": body.ticket_title,
        "TicketBody": body.ticket_body,
        "ValueToValidate": body.captcha_value,
        "UserEmailAddress": body.user_email or "",
    }

    try:
        resp = _requests.post(
            f"{USLUGI_BASE}/Tickets/SaveTicketFromPortalUser",
            data={"model": json.dumps(model)},
            cookies={"ASP.NET_SessionId": session_cookie} if session_cookie else {},
            headers={"Referer": USLUGI_BASE},
            timeout=15,
        )
        if resp.status_code == 400:
            raise HTTPException(status_code=400, detail="Invalid captcha or form data")
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="Failed to submit ticket to uslugi.gov.mk")
        return {"success": True, "ticket_id": resp.text.strip('"') if resp.text else None}
    except _requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not reach uslugi.gov.mk: {e}")


@router.post("/institutions/{slug}/connect", status_code=200)
def connect_institution(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not any(i["slug"] == slug for i in INSTITUTIONS):
        raise HTTPException(status_code=404, detail="Institution not found")
    disabled = _disabled_set(current_user)
    disabled.discard(slug)
    _save_disabled(current_user, disabled, db)
    return {"slug": slug, "connected": True}
