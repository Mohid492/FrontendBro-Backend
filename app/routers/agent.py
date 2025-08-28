from fastapi import status,APIRouter,HTTPException,Depends,BackgroundTasks,UploadFile, File
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from ..models import *
from ..schemas import *
from datetime import datetime
from typing import List
from ..agents.code_agent import code_agent as coding_agent
from langchain_community.chat_message_histories import RedisChatMessageHistory
from ..config import settings
import logging
from .auth.services import user_dependency
# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
router = APIRouter(
    prefix='/agent',
    tags=['agents']
)


def generate_session_id(user_id:int):
    return f"{user_id}_{int(datetime.now().timestamp())}"

async def store_chat(chat:ChatData,db: AsyncSession = Depends(get_session)):
    new_chat= ChatHistory(**chat.model_dump())
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)

@router.post('/create-new-session',status_code=status.HTTP_201_CREATED)
async def create_new_session(current_user: user_dependency, db: AsyncSession = Depends(get_session)):
    # First validating if the user exists
    result = await db.execute(select(User).filter(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session_id = generate_session_id(current_user.id)
    new_session = Session(
        user_id=current_user.id,
        session_id=session_id
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    session_id = new_session.session_id
    logger.info("New session created")
    return {"session_id": session_id}

@router.get('/get-sessions',response_model=List[Sessions],status_code=status.HTTP_200_OK)
async def get_user_sessions(current_user: user_dependency, db: AsyncSession = Depends(get_session)):
    result= await db.execute(select(Session).filter(Session.user_id == current_user.id).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    if not sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sessions found for the user")

    return sessions

@router.get('/get-chat-history',response_model=List[ChatDataResponse],status_code=status.HTTP_200_OK)
async def get_chat_history(current_user: user_dependency, session_id: str, db: AsyncSession = Depends(get_session)):

    result=await db.execute(select(ChatHistory).filter(ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id).order_by(ChatHistory.created_at.desc()))
    chat_history = result.scalars().all()
    if not chat_history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chat history found for the session")

    return chat_history

@router.delete('/delete-chat', status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    current_user: user_dependency,
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    # Fetch session
    session = await db.execute(
        select(Session).filter(Session.session_id == session_id, Session.user_id == current_user.id)
    )
    session_obj = session.scalars().first()

    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Fetch chat
    chat = await db.execute(
        select(ChatHistory).filter(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
    )
    chat_obj = chat.scalars().first()

    # If chat exists → delete chat + redis
    if chat_obj:
        await db.execute(
            delete(ChatHistory).where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
        )
        await db.commit()
        redis_chat_history = RedisChatMessageHistory(session_id=session_id, url=settings.REDIS_URL)
        await redis_chat_history.aclear()
        logger.info(f"Chat history for session {session_id} deleted for user {current_user.id}")

    # Always delete session (since it exists)
    await db.execute(
        delete(Session).where(Session.session_id == session_id, Session.user_id == current_user.id)
    )
    await db.commit()
    logger.info(f"Session {session_id} deleted for user {current_user.id}")

@router.post('/code-agent', status_code=status.HTTP_200_OK)
async def code_agent(current_user: user_dependency, prompt:str, db: AsyncSession = Depends(get_session)):
    # First validating if the user exists
    query = await db.execute(select(User).filter(User.id == current_user.id))
    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Getting the latest user session id
    session= await db.execute(
        select(Session).filter(Session.user_id == current_user.id).order_by(Session.created_at.desc()).limit(1)
    )
    session_obj= session.scalar_one_or_none()
    if session_obj is None:
        logger.info("No existing session found, creating a new one")
        latest_session_id=generate_session_id(current_user.id)
        new_session=Session(
            user_id=current_user.id,
            session_id=latest_session_id
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.session_id
    else:
        logger.info("Using existing session")
        session_id = session_obj.session_id

    res= await coding_agent(prompt, session_id)
    chat_data = ChatData(
        session_id=session_id,
        user_id=current_user.id,
        prompt=prompt,
        response=res
    )

    await store_chat(chat_data, db)
    logger.info("Chat data stored in the database")

    return res
