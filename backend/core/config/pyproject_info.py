from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class PyprojectConfig(BaseSettings):
    """The "project" section of the pyproject.toml file
    for loading the relevant data into the FastAPI app
    constructor for OpenAPI which

    NOTE: this may seem pointless and redundant,
    however this is important when the openapi axios client
    for the frontend is generated from the FastAPI app.
    """

    name: str
    version: str
    description: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: BaseSettings,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(cls),)

    model_config = SettingsConfigDict(
        toml_file='pyproject.toml',
        pyproject_toml_table_header=('project',),
        extra='ignore',
    )
