"""OAuth2 / JWT."""

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int | None = None
    jti: str | None = None
    iat: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
