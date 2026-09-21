from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


@database_sync_to_async
def get_user_from_token(token):
    # та же проверка, что и в REST API: подпись, срок, тип токена и is_active пользователя
    authentication = JWTAuthentication()
    try:
        validated = authentication.get_validated_token(token)
        return authentication.get_user(validated)
    except (TokenError, InvalidToken, AuthenticationFailed):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        token = parse_qs(scope.get("query_string", b"").decode()).get("token", [None])[0]

        if not token:
            headers = dict(scope.get("headers", []))
            authorization = headers.get(b"authorization", b"").decode()
            if authorization.lower().startswith("bearer "):
                token = authorization[7:].strip()

        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()

        return await super().__call__(scope, receive, send)