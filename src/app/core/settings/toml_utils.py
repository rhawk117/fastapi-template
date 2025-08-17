from pathlib import Path
from typing import Any

import toml
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from app.core.exceptions import RuntimeValidationError


def section_not_found_err(section_name: str) -> RuntimeError:
    return RuntimeError(
        f'The "{section_name}" section does not exist in the config file.\n'
        '\n\tFix: Check for a typo in the section name of the .toml file.'
    )


def read_toml(toml_file: Path) -> dict:
    """
    Reads a TOML file and returns its content as a dictionary.

    Parameters
    ----------
    toml_file : Path

    Returns
    -------
    dict

    Raises
    ------
    FileNotFoundError
    RuntimeError
    """
    if not toml_file.exists():
        raise FileNotFoundError(f'File not found: {toml_file}')

    file_text = toml_file.read_text(encoding='utf-8')
    try:
        return toml.loads(file_text)
    except toml.TomlDecodeError as exc:
        raise RuntimeError(
            f'Could not read the TOML file @{toml_file}.\nDetails: {exc}'
        )


def get_toml_section(name: str, toml_data: dict) -> dict:
    """
    given a toml section name (e.g) "app.settings", it resolves the section

    Example:
    >>> toml_data = {'app': {'settings': {'debug': True}}}
    >>> get_toml_section('app.settings', toml_data)
    >>> {'debug': True}

    Parameters
    ----------
    name : str
    toml_data : dict

    Returns
    -------
    dict

    Raises
    ------
    KeyError
    """
    parts = name.split('.')
    section = toml_data
    for part in parts:
        if part not in toml_data:
            raise section_not_found_err(name)

        section = toml_data[part]
    return section


def section_to_settings(
    settings_cls: type[BaseSettings],
    *,
    section_name: str,
    toml_data: dict
) -> Any:
    """
    Converts a toml section to a Pydantic settings class.

    Parameters
    ----------
    settings_cls : type[BaseSettings]
    section_name : str
    toml_data : dict

    Returns
    -------
    Any

    Raises
    ------
    RuntimeError
    RuntimeError
    """
    if not toml_data:
        raise RuntimeError('Nothing was loaded from the TOML file.')

    try:
        section = get_toml_section(section_name, toml_data)
    except KeyError as exc:
        raise RuntimeError(f"Section '{section_name}' not found in TOML data.") from exc

    try:
        settings = settings_cls.model_validate(section)
    except ValidationError as exc:
        raise RuntimeValidationError(exc)

    return settings
