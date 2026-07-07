import base64
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        username: str,
        password: str,
        exempt_paths: frozenset[str] | None = None,
        realm: str = "Willbe Trends",
    ):
        super().__init__(app)
        self.username = username
        self.password = password
        self.exempt_paths = exempt_paths or frozenset()
        self.realm = realm

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        if not self._is_authorized(request.headers.get("Authorization")):
            return Response(
                content="Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )

        return await call_next(request)

    def _is_authorized(self, authorization: str | None) -> bool:
        if not authorization or not authorization.startswith("Basic "):
            return False

        try:
            decoded = base64.b64decode(authorization[6:]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False

        username, separator, password = decoded.partition(":")
        if not separator:
            return False

        return secrets.compare_digest(username, self.username) and secrets.compare_digest(
            password, self.password
        )
