class MimpiTaniError(Exception):
    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message or message


class ValidationError(MimpiTaniError):
    pass


class DatabaseError(MimpiTaniError):
    pass


class WorkspaceNotInitializedError(MimpiTaniError):
    pass


class WeatherAdapterError(MimpiTaniError):
    pass


class OptimizerError(MimpiTaniError):
    pass
