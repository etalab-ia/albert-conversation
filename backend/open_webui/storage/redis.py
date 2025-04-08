from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.datastructures import MutableHeaders
from itsdangerous import URLSafeSerializer
import secrets
import logging

import copy

from open_webui.env import PROCONNECT_SESSION_DURATION
from open_webui.storage.redis_client import redis_client

log = logging.getLogger(__name__)

class RedisSessionMiddleware(SessionMiddleware):
    def __init__(self, app, secret_key, session_cookie="session", max_age=PROCONNECT_SESSION_DURATION):
        """Initialize the Redis Session Middleware."""
        self.redis = redis_client
        self.serializer = URLSafeSerializer(secret_key)
        # Convert max_age to integer seconds if it's a string
        if isinstance(max_age, str):
            try:
                max_age = int(max_age)
            except ValueError:
                max_age = 86400  # Default to 24 hours if conversion fails
        super().__init__(app, secret_key, session_cookie, max_age)
        log.debug(f"Initialized RedisSessionMiddleware with max_age: {max_age}")

    def get_session_id(self, scope: dict, receive) -> str:
        """Retrieve session id from cookies."""
        if scope["type"] == "websocket":
            # Extract cookies from WebSocket headers
            headers = dict(scope.get("headers", []))
            cookie_header = headers.get(b"cookie", b"").decode()
            if not cookie_header:
                return ""
            
            # Parse cookies manually for WebSocket
            cookies = {}
            for cookie in cookie_header.split("; "):
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies[key] = value
            return cookies.get(self.session_cookie, "")
        else:
            # Handle HTTP requests normally
            request = Request(scope, receive)
            return request.cookies.get(self.session_cookie, "")

    def write_session_data(self, session_id: str, session_data: dict):
        """Write session data to Redis."""
        try:
            data = self.serializer.dumps(session_data)
            # Ensure max_age is an integer
            max_age = int(self.max_age) if self.max_age else None
            self.redis.set(name=session_id, value=data, ex=max_age)
            log.debug(f"Session data written for ID {session_id}: {session_data}")
        except Exception as e:
            log.error(f"Error writing session data: {str(e)}")
            raise

    def get_valid_session_data(self, session_id: str) -> dict:
        """Retrieve and validate session data from Redis."""
        if not session_id:
            log.debug("No session ID provided")
            return {}

        try:
            data = self.redis.get(session_id)
            if not data:
                log.debug(f"No data found for session ID {session_id}")
                return {}

            session_data = self.serializer.loads(data)
            log.debug(f"Retrieved session data for ID {session_id}: {session_data}")
            return session_data
        except Exception as e:
            log.error(f"Error retrieving session data: {str(e)}")
            self.redis.delete(session_id)
            return {}

    async def __call__(self, scope: dict, receive, send) -> None:
        """Middleware entrypoint."""

        session_id = self.get_session_id(scope, receive)
        scope["session"] = self.get_valid_session_data(session_id)

        if not scope["session"] or not session_id:
            session_id = secrets.token_urlsafe()
            scope["session"] = {}  # Initialize an empty session
            set_cookie = True
        else:
            set_cookie = False

        original_session = copy.deepcopy(scope["session"])

        async def send_wrapper(message):
            nonlocal set_cookie
            if message["type"] == "http.response.start":
                current_session = scope["session"]

                if current_session != original_session:
                    self.write_session_data(session_id, current_session)
                    set_cookie = True

                if set_cookie:
                    headers = MutableHeaders(scope=message)
                    header_value = "{session_cookie}={session_id}; path={path}; {max_age}{security_flags}".format(
                        session_cookie=self.session_cookie,
                        session_id=session_id,
                        path=self.path,
                        max_age=f"Max-Age={self.max_age}; " if self.max_age else "",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)
