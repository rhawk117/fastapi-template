from typing import Annotated, NamedTuple

from pydantic import Field

from backend.common.types import AlphaString
from fastapi_template.core.pydantic import CustomBaseModel, FixedLengthString


class TokenResponse(CustomBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'
    expires_in: int


class LoginRequest(CustomBaseModel):
    username: Annotated[AlphaString, Field(..., description='Username of the user')]
    password: Annotated[
        FixedLengthString, Field(..., description='Password of the user')
    ]


class RefreshTokenRequest(CustomBaseModel):
    refresh_token: Annotated[
        FixedLengthString,
        Field(..., description='Refresh token to obtain new access token'),
    ]




class JwtToken(NamedTuple):
    token: str
    payload: dict
