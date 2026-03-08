from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.agents.graph import get_agent_graph
from app.agents.state import create_initial_state
from app.schemas.message import ChatRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Send a message and get a response from the agent system"""
    session_service = SessionService(db)
    message_service = MessageService(db)
    agent_graph = get_agent_graph()

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = request.session_id

        # Get conversation history (limited to last 10 messages for performance)
        messages = await message_service.get_messages_by_session(session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]  # Limit to last 10 messages
        ]
    else:
        new_session = await session_service.create_session({"title": None})
        session_id = new_session.id
        conversation_history = []

    try:
        # Prepare state for agent using factory function
        state = create_initial_state(str(session_id), request.message, conversation_history)

        # Run the agent graph
        final_state = await agent_graph.invoke(state)

        # Extract response
        response_content = final_state.get("response", "")
        sources = final_state.get("sources", [])

        # Handle error if any
        if final_state.get("error"):
            logger.error(f"Agent error: {final_state['error']}")

        # Save the exchange
        await message_service.save_exchange(
            session_id,
            request.message,
            response_content,
            {
                "type": "agent_response",
                "model": "qwen-via-langgraph",
                "sources": sources,
                "intent": final_state.get("user_intent", "unknown")
            }
        )

        # Update session
        await session_service.increment_message_count(session_id)

        return {
            "session_id": session_id,
            "response": response_content,
            "sources": sources
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")
