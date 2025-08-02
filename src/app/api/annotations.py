from typing import Annotated

from fastapi import Path

PathUUID = Annotated[str, Path(..., description='The unique id of this resource')]

