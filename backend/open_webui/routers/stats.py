import logging
from datetime import datetime

from open_webui.models.users import Users

from fastapi import APIRouter
from pydantic import BaseModel

from open_webui.internal.db import get_db
from sqlalchemy import text

log = logging.getLogger(__name__)

router = APIRouter()

class GlobalIndicators(BaseModel):
    total_users: int
    total_messages: int
    total_conversations: int

class CurrentStats(BaseModel):
    active_users: int
    model_usage: dict

class EvolutionStats(BaseModel):
    users_over_time: list[dict]
    conversations_over_time: list[dict]

class StatsResponse(BaseModel):
    global_indicators: GlobalIndicators
    current_stats: CurrentStats
    evolution_stats: EvolutionStats

def get_json_count_query():
    """Return the SQL query to count messages in all chats for PostgreSQL."""
    return """
        SELECT COUNT(*)
        FROM chat, LATERAL json_each(chat.chat->'history'->'messages') AS msg
        WHERE json_extract_path(chat.chat, 'history') IS NOT NULL
        AND json_extract_path(chat.chat, 'history', 'messages') IS NOT NULL
        AND json_typeof(chat.chat->'history'->'messages') = 'object'
    """

def get_model_usage_query():
    """Return the SQL query to count model usage for PostgreSQL."""
    return """
        SELECT 
            msg.value->>'model' as model,
            COUNT(*) as count
        FROM chat, LATERAL json_each(chat.chat->'history'->'messages') AS msg
        WHERE json_extract_path(chat.chat, 'history') IS NOT NULL
        AND json_extract_path(chat.chat, 'history', 'messages') IS NOT NULL
        AND json_typeof(chat.chat->'history'->'messages') = 'object'
        AND msg.value->>'role' = 'assistant' 
        AND json_extract_path(msg.value, 'model') IS NOT NULL
        GROUP BY msg.value->>'model'
        ORDER BY count DESC
    """

def get_users_evolution_query():
    """Return the SQL query for users evolution for PostgreSQL."""
    return """
        SELECT 
            DATE(to_timestamp(created_at)) as date,
            COUNT(*) as count
        FROM "user" 
        WHERE created_at > :threshold
        GROUP BY DATE(to_timestamp(created_at))
        ORDER BY date
    """

def get_conversations_evolution_query():
    """Return the SQL query for conversations evolution for PostgreSQL."""
    return """
        SELECT 
            DATE(to_timestamp(created_at)) as date,
            COUNT(*) as count
        FROM chat 
        WHERE created_at > :threshold
        GROUP BY DATE(to_timestamp(created_at))
        ORDER BY date
    """

@router.get("/", response_model=StatsResponse)
async def get_stats():
    """Get comprehensive statistics for the platform - TEMPORARILY DISABLED"""
    # TEMPORARY DISABLE: Stats endpoint causing database performance issues
    # Return minimal stats to prevent frontend errors
    return StatsResponse(
        global_indicators=GlobalIndicators(
            total_users=0,
            total_messages=0,
            total_conversations=0
        ),
        current_stats=CurrentStats(
            active_users=0,
            model_usage={}
        ),
        evolution_stats=EvolutionStats(
            users_over_time=[],
            conversations_over_time=[]
        )
    ) 