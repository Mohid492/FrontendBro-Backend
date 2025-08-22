from fastapi import status,APIRouter,HTTPException,Depends,BackgroundTasks
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from ..models import *
from ..schemas import *
from datetime import datetime
from typing import List
from ..agents.deepseek_agent import deepseek_agent
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

@router.delete('/delete-chat',status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(current_user: user_dependency,session_id:str,db: AsyncSession = Depends(get_session)):
    # Check if any chat exists for the user and session
    result = await db.execute(
        select(ChatHistory).filter(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
    )
    chat_obj = result.scalar_one_or_none()
    if not chat_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User/session not found")

    # Deleting all chat history of user in PostgreSQL and redis
    await db.execute(
        delete(ChatHistory).where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
    )
    await db.commit()
    # Now deleting the session
    await db.execute(delete(Session).filter(Session.session_id==session_id))
    await db.commit()
    # Now deleting from redis
    redis_chat_history=RedisChatMessageHistory(session_id=session_id,url=settings.REDIS_URL)
    await redis_chat_history.clear()
    logger.info(f"Chat history and session {session_id} deleted for user {current_user.id}")

@router.post('/deepseek-chat', status_code=status.HTTP_200_OK)
async def deepseek_chat(current_user: user_dependency,prompt:str,background_tasks: BackgroundTasks,db: AsyncSession = Depends(get_session)):
    # First validating if the user exists
    query = await db.execute(select(User).filter(User.id == current_user.id))
    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    is_new=False
    # Getting the latest user session id
    session= await db.execute(
        select(Session).filter(Session.user_id == current_user.id).order_by(Session.created_at.desc()).limit(1)
    )
    latest_session_id= session.scalar_one_or_none()
    if latest_session_id is None:
        latest_session_id=generate_session_id(current_user.id)

    session_id=latest_session_id

    res= await deepseek_agent(prompt,session_id)
    chat_data = ChatData(
        session_id=session_id,
        user_id=current_user.id,
        prompt=prompt,
        response=res
    )

    background_tasks.add_task(store_chat, chat_data, db)
    logger.info("Chat data stored in the database")

    return res
