from rest_framework.routers import DefaultRouter
from rest_framework.routers import Route


class ToggleObjectRouter(DefaultRouter):
    """
    A custom DRF router that adds two additional routes for enabling and disabling objects.

    This router extends the DefaultRouter and defines two PATCH endpoints for each registered viewset:
    - `{prefix}/{lookup}/enable/`: Calls the `enable` action on the object identified by `{lookup}`.
    - `{prefix}/{lookup}/disable/`: Calls the `disable` action on the object identified by `{lookup}`.

    These routes are intended for toggling the enabled/disabled state of an object via custom viewset actions.
    """
    routes = [
        Route(
            url=r"^{prefix}/{lookup}/enable{trailing_slash}$",
            mapping={
                "patch": "enable",
            },
            name="{basename}-enable",
            detail=True,
            initkwargs={},
        ),
        Route(
            url=r"^{prefix}/{lookup}/disable{trailing_slash}$",
            mapping={
                "patch": "disable",
            },
            name="{basename}-disable",
            detail=True,
            initkwargs={},
        ),
    ] + DefaultRouter.routes
