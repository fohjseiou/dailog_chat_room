from typing import Dict, Any, AsyncIterator, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.summary_service import SummaryService
from app.services.memory_extraction_service import MemoryExtractionService
from app.agents.graph import get_unified_agent_graph
from app.agents.state import create_initial_state
from app.schemas.message import ChatRequest
from app.dependencies import get_current_user
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send a message and get a response from the agent system.

    Uses LangGraph ainvoke for execution.
    """
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Get user_id from authenticated user, or None for anonymous
    user_id = current_user.id if current_user else None

    # Prepare session and history
    session_id, conversation_history = await _prepare_session(
        session_service, message_service, request, user_id
    )

    try:
        # Create initial state
        state = create_initial_state(
            user_message=request.message,
            conversation_history=conversation_history,
            user_id=user_id,
            session_id=session_id,
            streaming=False
        )

        # Execute graph using ainvoke
        agent_graph = get_unified_agent_graph()
        final_state = await agent_graph.ainvoke(state)

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
                "model": "qwen-langgraph",
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


async def _stream_chat_events(
    request: ChatRequest,
    db: AsyncSession,
    current_user: Optional[User] = None
) -> AsyncIterator[str]:
    """
    Generate SSE events for streaming chat

    Yields SSE-formatted events
    """
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Import nodes for direct use
    from app.agents.nodes import intent_router_node, rag_retriever_node, response_generator_node_stream

    # Get user_id from authenticated user, or None for anonymous
    user_id = current_user.id if current_user else None

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            yield _format_sse("error", {"error": "Session not found"})
            return
        session_id = request.session_id

        # Get conversation history
        messages = await message_service.get_messages_by_session(session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]
        ]
    else:
        new_session = await session_service.create_session({"title": None}, user_id=user_id)
        session_id = new_session.id
        conversation_history = []

    try:
        # Send session_id first
        yield _format_sse("session_id", {"session_id": session_id})

        # Prepare state with user_id
        state = create_initial_state(request.message, conversation_history, user_id=user_id)

        # Run the streaming workflow manually
        full_response = ""
        sources = []

        # Step 1: Intent routing
        intent_result = await intent_router_node(state)
        intent = intent_result.get("user_intent", "unknown")
        state.update(intent_result)
        yield _format_sse("intent", {"intent": intent})

        # Step 2: RAG retrieval if needed
        if intent == "legal_consultation":
            rag_result = await rag_retriever_node(state)
            state.update(rag_result)
            sources = rag_result.get("sources", [])
            yield _format_sse("context", {"sources": sources})

        # Step 3: Stream response
        async for chunk_event in response_generator_node_stream(state):
            yield _format_sse(chunk_event["event"], chunk_event["data"])

            if chunk_event["event"] == "end":
                full_response = chunk_event["data"].get("response", "")
            elif chunk_event["event"] == "error":
                full_response = "抱歉，处理您的请求时出现错误。"

        # Save the exchange
        if full_response:
            await message_service.save_exchange(
                session_id,
                request.message,
                full_response,
                {
                    "type": "agent_response_stream",
                    "model": "qwen-via-langgraph-stream",
                    "sources": sources,
                    "intent": intent
                }
            )

            # Update session
            await session_service.increment_message_count(session_id)

    except Exception as e:
        logger.error(f"Error in stream chat endpoint: {e}", exc_info=True)
        yield _format_sse("error", {"error": str(e)})


async def _prepare_session(
    session_service: SessionService,
    message_service: MessageService,
    request: ChatRequest,
    user_id: Optional[str]
) -> tuple[str, list[Dict]]:
    """
    Prepare session and conversation history.

    Returns:
        tuple of (session_id, conversation_history)
    """
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = await message_service.get_messages_by_session(request.session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]  # Limit to last 10 messages
        ]
        return request.session_id, conversation_history
    else:
        new_session = await session_service.create_session({"title": None}, user_id=user_id)
        return new_session.id, []


def _format_sse(event: str, data: Dict[str, Any]) -> str:
    """Format data as Server-Sent Event"""
    data_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {data_str}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> StreamingResponse:
    """
    Send a message and get a streaming response via Server-Sent Events

    SSE Events:
    - session_id: Initial session ID
    - intent: User's intent classification
    - context: Retrieved knowledge base context
    - token: Response text chunk
    - end: Response completed
    - error: Error occurred
    """
    return StreamingResponse(
        _stream_chat_events(request, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def _maybe_generate_summary(db: AsyncSession, session_id: str) -> None:
    """Check if summary should be generated and generate it asynchronously (legacy, kept for compatibility)"""
    try:
        summary_service = SummaryService(db)
        if await summary_service.should_generate_summary(session_id):
            logger.info(f"Triggering summary generation for session {session_id}")
            await summary_service.generate_summary(session_id)
    except Exception as e:
        logger.error(f"Error in background summary generation: {e}")


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the summary for a session

    Generates summary if it doesn't exist and the session has enough messages.

    - **session_id**: Session UUID
    """
    summary_service = SummaryService(db)

    # Check if session exists first
    from app.services.session_service import SessionService
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await summary_service.get_summary(session_id)

    if summary is None:
        return {
            "session_id": session_id,
            "summary": None,
            "message": "No summary available. Session needs more messages."
        }

    return {
        "session_id": session_id,
        "summary": summary
    }


@router.post("/sessions/{session_id}/summary/regenerate")
async def regenerate_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Force regenerate the summary for a session

    - **session_id**: Session UUID
    """
    summary_service = SummaryService(db)

    # Check if session exists first
    from app.services.session_service import SessionService
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await summary_service.regenerate_summary(session_id)

    return {
        "session_id": session_id,
        "summary": summary,
        "message": "Summary regenerated successfully"
    }


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    End a session and trigger final summary generation for long-term memory.

    This should be called when user leaves a session or navigates away.

    - **session_id**: Session UUID
    """
    from app.services.session_service import SessionService

    # Check if session exists and user has access
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check ownership
    if current_user and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = current_user.id if current_user else session.user_id

    # Generate final summary for long-term memory
    if user_id:
        try:
            extraction_service = MemoryExtractionService(db)
            summary = await extraction_service.generate_and_store_summary(user_id, session_id)

            return {
                "session_id": session_id,
                "summary": summary,
                "message": "Session ended. Summary saved to long-term memory."
            }
        except Exception as e:
            logger.error(f"Error generating final summary: {e}")
            return {
                "session_id": session_id,
                "message": "Session ended, but summary generation failed."
            }

    return {
        "session_id": session_id,
        "message": "Session ended."
    }
