import logging
from collections.abc import Iterable

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model
from django.db.models import ProtectedError
from django.db.models import RestrictedError
from django.http import Http404

from rest_framework import exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler as drf_exception_handler

from gardeniq.base.exceptions import ProtectedException

logger = logging.getLogger(__name__)


class DoesNotExistAPIException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A related object does not exist."
    default_code = "does_not_exist"


class ProtectedAPIException(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This object is used by other objects and cannot be deleted."
    default_code = "protected"


class ServerErrorAPIException(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal server error."
    default_code = "server_error"


def _blocking_objects(objects: Iterable[Model]) -> dict[str, list[str]]:
    """Group the objects that block a deletion by model, e.g. {"devices": ["Device `Card` : …"]}."""
    grouped: dict[str, list[str]] = {}
    for obj in objects:
        grouped.setdefault(str(obj._meta.verbose_name_plural), []).append(str(obj))
    return {model: sorted(names) for model, names in grouped.items()}


def _to_api_exception(exc: Exception) -> tuple[exceptions.APIException, dict[str, list[str]]]:
    """Translate any exception into a DRF exception, with the `errors` it carries when it is not a validation one."""
    if isinstance(exc, exceptions.APIException):
        return exc, {}
    if isinstance(exc, Http404):
        return exceptions.NotFound(*exc.args), {}
    if isinstance(exc, DjangoPermissionDenied):
        return exceptions.PermissionDenied(*exc.args), {}
    if isinstance(exc, DjangoValidationError):
        return exceptions.ValidationError(as_serializer_error(exc)), {}
    if isinstance(exc, ObjectDoesNotExist):
        return DoesNotExistAPIException(str(exc)), {}
    if isinstance(exc, ProtectedError):
        return ProtectedAPIException(), _blocking_objects(exc.protected_objects)
    if isinstance(exc, RestrictedError):
        return ProtectedAPIException(), _blocking_objects(exc.restricted_objects)
    if isinstance(exc, ProtectedException):
        return ProtectedAPIException(str(exc)), {}
    return ServerErrorAPIException(), {}


def exception_handler(exc: Exception, context: dict[str, object]) -> Response | None:
    """
    Global exception handler of the API (`REST_FRAMEWORK["EXCEPTION_HANDLER"]`).

    Every error gets the same body: `{"status": <int>, "code": <str>, "message": <str>, "errors": <dict>}`.
    - DRF exceptions keep their status and code (`invalid`, `not_authenticated`, `not_found`, `throttled`…).
    - Django `ValidationError` -> 400 `invalid`, `ObjectDoesNotExist` -> 400 `does_not_exist`.
    - Django `ProtectedError` / `RestrictedError` and `ProtectedException` -> 409 `protected`; for the Django ones,
      `errors` lists the blocking objects by model.
    - Any other exception -> 500 `server_error` with a generic message: the details are only logged.
      With `DEBUG`, it returns None instead: DRF re-raises the exception and Django shows its debug page.

    Validation errors go to `errors` by field, the non-field ones under `non_field_errors`; `errors` is `{}` otherwise.
    """
    api_exc, errors = _to_api_exception(exc)
    if isinstance(api_exc, ServerErrorAPIException):
        if settings.DEBUG:
            return None
        logger.error("Unhandled exception in %r", context.get("view"), exc_info=exc)

    # DRF builds the response: status, `WWW-Authenticate` and `Retry-After` headers, transaction rollback.
    response = drf_exception_handler(api_exc, context)
    assert response is not None, "DRF handles every APIException"

    detail = api_exc.detail
    if isinstance(detail, (list, dict)):
        code = str(api_exc.default_code)
        message = str(api_exc.default_detail)
        body_errors = detail if isinstance(detail, dict) else {str(api_settings.NON_FIELD_ERRORS_KEY): detail}
    else:
        code = str(api_exc.get_codes())
        message = str(detail)
        body_errors = errors

    response.data = {"status": response.status_code, "code": code, "message": message, "errors": body_errors}
    return response
