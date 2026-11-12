import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from django.db.models import RestrictedError
from django.http import Http404

from rest_framework import exceptions
from rest_framework import status

import pytest

from gardeniq.base.exception_handler import exception_handler
from gardeniq.base.exceptions import DeleteProtectedException
from gardeniq.base.models import Status

CONTEXT = {"view": None, "request": None}


class TestExceptionHandler:

    def test_drf_validation_error_lists_errors_by_field(self):
        """A DRF validation error gives a 400 `invalid` with the errors of each field."""
        # GIVEN
        exc = exceptions.ValidationError({"name": ["This field is required."]})

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "status": 400,
            "code": "invalid",
            "message": "Invalid input.",
            "errors": {"name": ["This field is required."]},
        }

    def test_drf_validation_error_without_field_goes_to_non_field_errors(self):
        """A validation error not tied to a field is listed under `non_field_errors`."""
        # GIVEN
        exc = exceptions.ValidationError("Bad input.")

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.data["errors"] == {"non_field_errors": ["Bad input."]}

    @pytest.mark.parametrize(
        "exc, expected_status, expected_code, expected_message",
        [
            (exceptions.NotAuthenticated(), 401, "not_authenticated", "Authentication credentials were not provided."),
            (exceptions.NotFound(), 404, "not_found", "Not found."),
            (Http404(), 404, "not_found", "Not found."),
            (DjangoPermissionDenied(), 403, "permission_denied", "You do not have permission to perform this action."),
            (exceptions.MethodNotAllowed("PATCH"), 405, "method_not_allowed", 'Method "PATCH" not allowed.'),
        ],
        ids=["not-authenticated", "drf-not-found", "django-http404", "django-permission-denied", "method-not-allowed"],
    )
    def test_simple_errors_keep_their_status_and_code(self, exc, expected_status, expected_code, expected_message):
        """DRF and Django errors keep their status and code, with their message and no `errors`."""
        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == expected_status
        assert response.data == {
            "status": expected_status,
            "code": expected_code,
            "message": expected_message,
            "errors": {},
        }

    def test_authentication_header_is_kept(self):
        """The `WWW-Authenticate` header set by DRF on a 401 is kept."""
        # GIVEN
        exc = exceptions.NotAuthenticated()
        exc.auth_header = "Token"

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response["WWW-Authenticate"] == "Token"

    def test_throttled_keeps_retry_after_header(self):
        """A throttled request gives a 429 `throttled` with its `Retry-After` header."""
        # GIVEN
        exc = exceptions.Throttled(wait=10)

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data["code"] == "throttled"
        assert response["Retry-After"] == "10"

    @pytest.mark.parametrize(
        "exc, expected_errors",
        [
            (
                DjangoValidationError({"pin": "Pin 3 is already used by a sensor."}),
                {"pin": ["Pin 3 is already used by a sensor."]},
            ),
            (DjangoValidationError("Invalid datasheet."), {"non_field_errors": ["Invalid datasheet."]}),
        ],
        ids=["by-field", "without-field"],
    )
    def test_django_validation_error_gives_400(self, exc, expected_errors):
        """A Django validation error raised by a model gives a 400 `invalid`, like a DRF one."""
        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid"
        assert response.data["errors"] == expected_errors

    def test_object_does_not_exist_gives_400(self):
        """An object missing in business code gives a 400 `does_not_exist` with the exception message."""
        # GIVEN
        exc = Status.DoesNotExist("No device status found.")

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "status": 400,
            "code": "does_not_exist",
            "message": "No device status found.",
            "errors": {},
        }

    @pytest.mark.parametrize("error_class", [ProtectedError, RestrictedError], ids=["protected", "restricted"])
    def test_django_protected_error_lists_blocking_objects(self, error_class):
        """A deletion blocked by Django gives a 409 `protected` that lists the blocking objects by model."""
        # GIVEN
        blocking = [Status(name="Online", tag="device"), Status(name="Offline", tag="device")]
        exc = error_class("Cannot delete some instances.", blocking)

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data == {
            "status": 409,
            "code": "protected",
            "message": "This object is used by other objects and cannot be deleted.",
            "errors": {"statuses": ["Status `Offline` : device", "Status `Online` : device"]},
        }

    def test_project_protected_exception_gives_409(self):
        """A `ProtectedException` of the project gives a 409 `protected` with its message."""
        # GIVEN
        exc = DeleteProtectedException()

        # WHEN
        response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data == {
            "status": 409,
            "code": "protected",
            "message": "This object is used by other objects and cannot be deleted.",
            "errors": {},
        }

    def test_unexpected_exception_gives_generic_500_and_is_logged(self, caplog):
        """Any other exception gives a generic 500 `server_error`: its details are only in the logs."""
        # GIVEN
        exc = ValueError("secret detail")

        # WHEN
        with caplog.at_level(logging.ERROR, logger="gardeniq.base.exception_handler"):
            response = exception_handler(exc, CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == {
            "status": 500,
            "code": "server_error",
            "message": "Internal server error.",
            "errors": {},
        }
        assert "secret detail" not in str(response.data)
        assert caplog.records[-1].exc_info[1] is exc

    def test_unexpected_exception_is_left_to_django_in_debug(self, settings, caplog):
        """With DEBUG, an unexpected exception is not handled, so Django shows its debug page with the traceback."""
        # GIVEN
        settings.DEBUG = True

        # WHEN
        with caplog.at_level(logging.ERROR, logger="gardeniq.base.exception_handler"):
            response = exception_handler(ValueError("secret detail"), CONTEXT)

        # THEN
        assert response is None
        assert not caplog.records

    def test_known_error_stays_json_in_debug(self, settings):
        """With DEBUG, an expected error keeps its JSON body: only the unexpected ones are left to Django."""
        # GIVEN
        settings.DEBUG = True

        # WHEN
        response = exception_handler(DeleteProtectedException(), CONTEXT)

        # THEN
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "protected"
