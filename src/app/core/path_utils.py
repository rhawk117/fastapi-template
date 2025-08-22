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

def root_file_path(file: str | Path) -> Path:
    """Takes a file name and returns it's absolute path relative to the root of the project.

    Arguments:
        file {str | Path} -- the file name to resolve
    Returns:
        Path -- the absolute path to the file
    """
    path = get_app_root().joinpath(file)
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')
    return path.resolve()
