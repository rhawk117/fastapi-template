


import functools
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_settings import (
    SettingsConfigDict,
)

from app.core.settings import YamlSettingsLoader


class ServerInfo(BaseModel):
    url: Annotated[str, Field(description="URL of the server")]
    description: Annotated[
        str | None, Field(description="Description of the server")] = None
    variables: Annotated[
        dict[str, dict] | None,
        Field(description="Variables for the server")
    ] = None

class ApiDocRoutes(BaseModel):
    openapi: Annotated[str, Field(description="openapi url path")] = '/openapi.json'
    redoc: Annotated[str, Field(description="redoc url path")] = '/redoc'
    swagger: Annotated[str, Field(description="swagger url path")] = '/docs'


class Contact(BaseModel):
    name: Annotated[
        str, Field(description='Name of the contact person or organization')
    ]
    email: Annotated[
        str, Field(description='Email of the contact person or organization')
    ]
    url: Annotated[str, Field(description='URL of the contact person or organization')]

class LicenseInfo(BaseModel):
    name: Annotated[str, Field(description='Name of the license')]
    url: Annotated[str | None, Field(description='URL of the license')] = None
    identifier: Annotated[
        str | None, Field(description='Identifier of the license, if applicable')
    ] = None



class ApiSpecYAML(YamlSettingsLoader):
    model_config = SettingsConfigDict(
        yaml_file=['fastapi.yaml'],
        env_nested_delimiter='__',
    )


    title: str = 'FastAPI'
    version: str = '0.1.0'
    description: str = ''
    summary: str | None

    terms_of_service: str | None = None

    contact: Contact | None = None

    openapi_prefix: str = ''

    docs: ApiDocRoutes = ApiDocRoutes()

    root_path: str = ''

    root_path_in_servers: bool = True

    redirect_slashes: bool = True

    servers: list[ServerInfo] | None = None

    license_info: LicenseInfo | None = None

    def get_fastapi_kwargs(self) -> dict:
        """
        Converts the metadata to a dictionary suitable for FastAPI settings.

        Returns
        -------
        dict[str, str | bool]
            A dictionary with the metadata fields.
        """
        dumped = self.model_dump(exclude={'urls'})
        dumped.update({
            'docs_url': self.docs.swagger,
            'redoc_url': self.docs.redoc,
            'openapi_url': self.docs.openapi,
        })
        return dumped

@functools.lru_cache
def get_api_spec() -> ApiSpecYAML:
    """
    Returns a singleton instance of ApiSpecYAML.
    This function caches the instance to avoid reloading it multiple times.

    Returns
    -------
    ApiSpecYAML
        The API specification settings.
    """
    return ApiSpecYAML()  # type: ignore[return-value]