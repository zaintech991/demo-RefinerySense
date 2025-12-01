"""API routes for AI chat assistant."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ChatMessage, ChatResponse
from app.services.ai_assistant import ai_assistant

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """Chat with AI assistant."""
    # Extract asset ID from message if mentioned (simplified)
    asset_id = None
    # In a real implementation, you might parse the message to extract asset references
    
    response = await ai_assistant.answer_question(
        db,
        message.message,
        asset_id,
        message.conversation_id
    )
    
    return ChatResponse(
        response=response["response"],
        conversation_id=response["conversation_id"]
    )

