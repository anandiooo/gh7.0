class TetaniError(Exception):
    # Dummy comment to force reload 3
    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message or message


class ValidationError(TetaniError):
    pass


class SystemError(TetaniError):
    pass


class DatabaseError(SystemError):
    pass


class ConflictError(TetaniError):
    pass


class NotFoundError(TetaniError):
    pass


class WorkspaceNotInitializedError(TetaniError):
    pass


class WeatherAdapterError(TetaniError):
    pass


class OptimizerError(TetaniError):
    pass
