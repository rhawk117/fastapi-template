from typing import Any

import msgspec
from fastapi.responses import JSONResponse


class MsgspecJSONResponse(JSONResponse):
    """
    Custom JSON response class that uses msgspec for serialization.
    """

    media_type = 'application/json'

    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)
