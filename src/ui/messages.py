from src.errors import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.i18n.translator import t


def user_safe_error_message(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return t("error.validation")
    if isinstance(error, ConflictError):
        return t("error.conflict")
    if isinstance(error, NotFoundError):
        return t("error.not_found")
    if isinstance(error, DatabaseError):
        return t("error.database")
    return t("error.system")


__all__ = ["user_safe_error_message"]
