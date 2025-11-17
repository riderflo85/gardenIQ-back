from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from gardeniq.__version__ import Version
from gardeniq.__version__ import garden_firmware_version
from gardeniq.__version__ import micropython_version
from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel
from gardeniq.base.models import Status
from gardeniq.hardware.protocols.settings import pattern_strict_version


class Device(NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
    """

    uid = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="device uid",
        help_text="Unique device card UID (e.g: '12AB34567890DEAD').",
    )
    path = models.CharField(
        max_length=64,
        validators=[RegexValidator(settings.PATTERN_SERIAL_PORT)],
        verbose_name="card port path",
        help_text="Path of this card.",
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name="last seen",
        help_text="Datetime of the last communication.",
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        limit_choices_to=models.Q(tag__icontains="device"),
        related_name="devices",
        verbose_name="status",
    )
    gd_firmware_version = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(pattern_strict_version)],
        verbose_name="GardenIQ firmware version",
    )
    mp_firmware_version = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(pattern_strict_version)],
        verbose_name="MicroPython firmware version",
    )
    need_upgrade = models.BooleanField(
        default=False,
        verbose_name="need upgrade",
        help_text="Indicates if the device requires a firmware upgrade.",
    )

    def __str__(self) -> str:
        return f"Device `{self.name}` : {self.uid} : {self.path}"

    def _check_update(self, run_validator: bool = True) -> bool:
        """
        Check if firmware updates are available for the device.

        Compares the current firmware versions stored in the database (gd_firmware_version
        and mp_firmware_version) against the latest available versions (garden_firmware_version
        and micropython_version).

        Args:
            run_validator (bool, optional): Whether to run validation on version parsing.
                Defaults to True.

        Returns:
            bool: True if either the garden firmware or micropython firmware has a newer
                version available, False otherwise. Returns False if current versions are
                not set or if version parsing fails.

        Raises:
            No exceptions are raised; ValueError and AttributeError are caught internally
            and result in a False return value.
        """
        if not self.gd_firmware_version or not self.mp_firmware_version:
            return False

        try:
            gd_current_db_version_obj = Version(self.gd_firmware_version)
            mp_current_db_version_obj = Version(self.mp_firmware_version)
            latest_gd_version_obj = Version(garden_firmware_version, run_validator)
            latest_mp_version_obj = Version(micropython_version, run_validator)
            return (gd_current_db_version_obj < latest_gd_version_obj) or (
                mp_current_db_version_obj < latest_mp_version_obj
            )
        except (ValueError, AttributeError):
            return False

    def mark_online(self, on: bool = True) -> None:
        """
        Mark the device as online or offline by updating its status.
        This method updates the device's status to either ONLINE or OFFLINE based on the
        provided parameter. It queries the Status model to find the appropriate status
        object that matches both the device tag and the status name from settings.
        Args:
            on (bool, optional): If True, marks the device as online. If False, marks
                the device as offline. Defaults to True.
        Returns:
            None
        Raises:
            Status.DoesNotExist: If no matching status is found in the database with
                the specified tag and name criteria.
        Example:
            >>> device = Device.objects.get(id=1)
            >>> device.mark_online()  # Marks device as online
            >>> device.mark_online(False)  # Marks device as offline
        """
        status_enum = settings.DEFAULT_STATUS.ONLINE if on else settings.DEFAULT_STATUS.OFFLINE
        device_status = Status.objects.get(models.Q(tag__icontains="device") & models.Q(name=status_enum.value))
        self.status = device_status
        self.save()

    def set_firmware_versions(self, garden_fw: str, micropython_fw: str) -> None:
        error_msg = "Enter a valid value. Field : {f} | Bad value : {v}"
        validator = RegexValidator(pattern_strict_version)
        try:
            validator(garden_fw)
            validator(micropython_fw)
        except Exception as e:
            raise ValueError(
                error_msg.format(field="firmware_versions", value=f"gd={garden_fw}, mp={micropython_fw}")
            ) from e

        has_changed = self.gd_firmware_version != garden_fw or self.mp_firmware_version != micropython_fw
        if has_changed:
            self.gd_firmware_version = garden_fw
            self.mp_firmware_version = micropython_fw
            self.need_upgrade = self._check_update()
            self.save()
