import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.models.chat import ChatSession
from backend.schemas.chat import ChatRequest, ChatResponse, SessionOut, SessionDetailOut, SessionUpdate
from backend.services.chat_service import chat_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        disabled = {s.strip() for s in (current_user.disabled_institutions or "").split(",") if s.strip()}
        reply, session_id, portal_errors = await chat_service.chat(
            user_id=current_user.id,
            message=body.message,
            db=db,
            session_id=body.session_id,
            disabled_institutions=disabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        portal_errors=portal_errors,
    )


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailOut)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    from backend.models.chat import Message

    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
        .options(joinedload(ChatSession.messages))
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Limit to the last 200 messages to guarantee fast load times
    # (a typical conversation is 20-40 messages)
    if len(session.messages) > 200:
        session.messages = session.messages[-200:]

    return session


@router.patch("/sessions/{session_id}", response_model=SessionOut)
def rename_session(
    session_id: int,
    body: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = body.title[:60]
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
