from pydantic import ValidationError

from app.core.pydantic import parse_validation_error


class BuildFailedError(RuntimeError):
    """
    A human readable error that occurs when a build fails
    """

    def __init__(self, message: str) -> None:
        super().__init__(f'\nrange_monitor.BuildFailError: \n{message}')


class RuntimeValidationError(RuntimeError):
    """
    A human readable pydantic validation error that occurs
    when a settings class loaded is invalid.
    """

    def __init__(self, orig_exc: ValidationError) -> None:
        errors = parse_validation_error(orig_exc)
        message = [str(error) for error in errors]
        super().__init__(f'\nrange_monitor.RuntimeValidationError: \n{message}')


class InfrastructureError(RuntimeError):
    """
    A human readable error that occurs when there is an issue
    with the infrastructure, such as a missing file or directory.
    """

    def __init__(self, message: str) -> None:
        super().__init__(f'\nrange_monitor.InfrastructureError: \n{message}')
