from pathlib import Path


def abs_root_path(file: str | Path) -> Path:
    """Takes a file name and relative to the root of the project
    returns it's absolute path.

    Arguments:
        file {str | Path} -- the file name to resolve
    Returns:
        Path -- the absolute path to the file
    """
    if isinstance(file, str):
        file = Path(file)
    path = Path.cwd().joinpath(file)
    return path.resolve()


def get_app_root() -> Path:
    return Path(__file__).parent.parent.parent.resolve()


print(get_app_root())