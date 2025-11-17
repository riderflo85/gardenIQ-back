from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gardeniq.base"

    def ready(self) -> None:
        # Import versions this to ensure that requests to many github repot have been successfully completed.
        from gardeniq.__version__ import __version__  # noqa
        from gardeniq.__version__ import garden_firmware_version  # noqa
        from gardeniq.__version__ import micropython_version  # noqa
