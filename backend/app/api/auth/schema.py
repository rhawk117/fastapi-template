import time
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field

from backend.common.schemas import RequestSchema, ResponseSchema
from backend.common.types import AlphaString
from backend.core.security.fingerprint import ClientFingerprint


class LoginBody(RequestSchema):
    username: Annotated[
        AlphaString, Field(..., description='The username of the user to login')
    ]
    password: Annotated[
        AlphaString, Field(..., description='The password of the user to login')
    ]


class SessionIdentity(ResponseSchema):
    username: Annotated[
        str, Field(..., description='The username of the users session')
    ]
    role: Annotated[str, Field(..., description='The role of the user')]


class SessionData(BaseModel):
    """A model to represent the dictionary encrypted and stored in the redis
    store that represents a session.
    """

    identity: Annotated[
        SessionIdentity,
        Field(..., description='the identity of the user associated with the API key'),
    ]

    created_at: Annotated[
        float,
        Field(
            ...,
            description='The time the session was created in seconds ( time.tme() )',
        ),
    ]

    client: Annotated[
        ClientFingerprint,
        Field(..., description='The metadata of the identity of the user'),
    ]

    @classmethod
    def create(cls, username: str, role: str, client: ClientFingerprint) -> 'Self':
        return cls(
            identity=SessionIdentity(
                username=username,
                role=role,
            ),
            created_at=time.time(),
            client=client,
        )

    def trusts_client(self, client: ClientFingerprint) -> bool:
        return self.client == client


class SessionResponse(ResponseSchema):
    session_id: Annotated[
        str, Field(..., description='the signed API key to be issued to the client')
    ]
    identity: Annotated[
        SessionIdentity,
        Field(..., description='the identity of the user associated with the API key'),
    ]


class SessionHealth(ResponseSchema):
    max_age_at: Annotated[
        datetime,
        Field(
            ..., description='the time the session expires in seconds ( time.tme() )'
        ),
    ]
    expires_next: Annotated[
        datetime,
        Field(
            ...,
            description='the time the session expires in seconds ( time.tme() )',
        ),
    ]
    issued_at: Annotated[
        datetime,
        Field(
            ...,
            description='the time the session was created in seconds ( time.tme() )',
        ),
    ]


class SessionInfo(ResponseSchema):
    """A model to represent the information stored in the redis store"""

    owner: Annotated[
        SessionIdentity | None,
        Field(..., description='the identity of the user associated with the API key'),
    ]
    health: Annotated[
        SessionHealth,
        Field(
            ..., description='the health of the API key with the relevant timestamps'
        ),
    ]


class LogoutResponse(ResponseSchema):
    """A model to represent the response after a successful logout"""

    message: Annotated[
        str,
        Field(
            ...,
            description='the message to be sent to the client after a successful logout',
        ),
    ] = 'You have been logged out successfully'
    success: bool = True
