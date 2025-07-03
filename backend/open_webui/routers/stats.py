import logging
from datetime import datetime
from typing import Optional
from enum import Enum

from open_webui.models.users import Users

from fastapi import APIRouter, Query
from pydantic import BaseModel

from open_webui.internal.db import get_db
from sqlalchemy import text

log = logging.getLogger(__name__)

router = APIRouter()

class TimePeriod(str, Enum):
    WEEK = "1w"
    MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ALL_TIME = "all"

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

def get_time_threshold(period: TimePeriod) -> Optional[int]:
    """Calculate the timestamp threshold based on the selected period."""
    if period == TimePeriod.ALL_TIME:
        return None
    
    current_time = int(datetime.now().timestamp())
    
    if period == TimePeriod.WEEK:
        return current_time - (7 * 24 * 60 * 60)
    elif period == TimePeriod.MONTH:
        return current_time - (30 * 24 * 60 * 60)
    elif period == TimePeriod.THREE_MONTHS:
        return current_time - (90 * 24 * 60 * 60)
    elif period == TimePeriod.SIX_MONTHS:
        return current_time - (180 * 24 * 60 * 60)
    
    return None

def get_json_count_query(time_threshold: Optional[int] = None):
    """Return the SQL query to count messages in all chats for PostgreSQL."""
    base_query = """
        SELECT COUNT(*)
        FROM chat, LATERAL json_each(chat.chat->'history'->'messages') AS msg
        WHERE json_extract_path(chat.chat, 'history') IS NOT NULL
        AND json_extract_path(chat.chat, 'history', 'messages') IS NOT NULL
        AND json_typeof(chat.chat->'history'->'messages') = 'object'
    """
    
    if time_threshold:
        base_query += " AND chat.created_at > :threshold"
    
    return base_query

def get_model_usage_query(time_threshold: Optional[int] = None):
    """Return the SQL query to count model usage for PostgreSQL."""
    base_query = """
        SELECT 
            msg.value->>'model' as model,
            COUNT(*) as count
        FROM chat, LATERAL json_each(chat.chat->'history'->'messages') AS msg
        WHERE json_extract_path(chat.chat, 'history') IS NOT NULL
        AND json_extract_path(chat.chat, 'history', 'messages') IS NOT NULL
        AND json_typeof(chat.chat->'history'->'messages') = 'object'
        AND msg.value->>'role' = 'assistant' 
        AND json_extract_path(msg.value, 'model') IS NOT NULL
    """
    
    if time_threshold:
        base_query += " AND chat.created_at > :threshold"
    
    base_query += """
        GROUP BY msg.value->>'model'
        ORDER BY count DESC
    """
    
    return base_query

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

def get_total_users_query(time_threshold: Optional[int] = None):
    """Return the SQL query to count total users for PostgreSQL."""
    base_query = "SELECT COUNT(*) FROM \"user\""
    
    if time_threshold:
        base_query += " WHERE created_at > :threshold"
    
    return base_query

def get_total_conversations_query(time_threshold: Optional[int] = None):
    """Return the SQL query to count total conversations for PostgreSQL."""
    base_query = "SELECT COUNT(*) FROM chat"
    
    if time_threshold:
        base_query += " WHERE created_at > :threshold"
    
    return base_query

@router.get("/", response_model=StatsResponse)
async def get_stats(
    period: TimePeriod = Query(TimePeriod.ALL_TIME, description="Time period for statistics")
):
    """Get comprehensive statistics for the platform - publicly accessible"""
    
    time_threshold = get_time_threshold(period)
    
    # Global indicators
    with get_db() as db:
        if time_threshold:
            total_users = db.execute(text(get_total_users_query(time_threshold)), {"threshold": time_threshold}).scalar()
            total_conversations = db.execute(text(get_total_conversations_query(time_threshold)), {"threshold": time_threshold}).scalar()
        else:
            total_users = Users.get_num_users()
            total_conversations = db.execute(text("SELECT COUNT(*) FROM chat")).scalar()
        
        # Get total messages by counting all messages in all chats
        try:
            if time_threshold:
                total_messages_result = db.execute(text(get_json_count_query(time_threshold)), {"threshold": time_threshold}).scalar()
            else:
                total_messages_result = db.execute(text(get_json_count_query())).scalar()
        except Exception as e:
            log.error(f"Error counting messages: {e}")
            total_messages_result = 0
        total_messages = total_messages_result or 0
    
    # Current active users (users active in last 24 hours)
    current_time = int(datetime.now().timestamp())
    active_threshold = current_time - (24 * 60 * 60)  # 24 hours ago
    
    with get_db() as db:
        try:
            active_users_query = '''
                SELECT COUNT(*) FROM "user" 
                WHERE last_active_at > :threshold
            '''
            active_users = db.execute(text(active_users_query), {"threshold": active_threshold}).scalar()
        except Exception as e:
            log.error(f"Error counting active users: {e}")
            active_users = 0
    
    # Model usage stats - extract from actual chat data
    with get_db() as db:
        try:
            if time_threshold:
                model_usage_result = db.execute(text(get_model_usage_query(time_threshold)), {"threshold": time_threshold}).fetchall()
            else:
                model_usage_result = db.execute(text(get_model_usage_query())).fetchall()
        except Exception as e:
            log.error(f"Error getting model usage: {e}")
            model_usage_result = []
    
    # Convert to dictionary format
    model_usage = {}
    for row in model_usage_result:
        model_name = row[0]
        count = row[1]
        if model_name:  # Only include non-null model names
            model_usage[model_name] = count
    
    # Evolution stats - use the period threshold or default to 90 days for better visibility
    evolution_threshold = time_threshold or (current_time - (90 * 24 * 60 * 60))
    
    with get_db() as db:
        try:
            users_evolution = db.execute(text(get_users_evolution_query()), {"threshold": evolution_threshold}).fetchall()
        except Exception as e:
            log.error(f"Error getting users evolution: {e}")
            users_evolution = []
            
        try:
            conversations_evolution = db.execute(text(get_conversations_evolution_query()), {"threshold": evolution_threshold}).fetchall()
        except Exception as e:
            log.error(f"Error getting conversations evolution: {e}")
            conversations_evolution = []
    
    users_over_time = [{"date": row[0], "count": row[1]} for row in users_evolution]
    conversations_over_time = [{"date": row[0], "count": row[1]} for row in conversations_evolution]
    
    return StatsResponse(
        global_indicators=GlobalIndicators(
            total_users=total_users,
            total_messages=total_messages,
            total_conversations=total_conversations
        ),
        current_stats=CurrentStats(
            active_users=active_users,
            model_usage=model_usage
        ),
        evolution_stats=EvolutionStats(
            users_over_time=users_over_time,
            conversations_over_time=conversations_over_time
        )
    ) 