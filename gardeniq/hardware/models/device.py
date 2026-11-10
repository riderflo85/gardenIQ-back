from django.apps import apps
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db import transaction

from gardeniq.__version__ import Version
from gardeniq.__version__ import garden_firmware_version
from gardeniq.__version__ import micropython_version
from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel
from gardeniq.base.models import SeederMixinModel
from gardeniq.base.models import Status
from gardeniq.hardware.protocols.settings import pattern_strict_version
from gardeniq.hardware.validations import jsonschema_validation


class DeviceCategory(SeederMixinModel, NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `seed_id`
      - `is_ready`
      - `name`
      - `description`:optional
    """

    pins_configuration = models.JSONField(
        verbose_name="pins configuration",
        help_text="JSON object describing the pins configuration of this device category.",
    )

    class Meta:
        verbose_name = "device category"
        verbose_name_plural = "device categories"

    def __str__(self) -> str:
        return f"DeviceCategory `{self.name}`"

    def clean(self) -> None:
        """
        Validate the pins_configuration JSON field against the DATASHEET_JSON_SCHEMA during `full_clean()`,
        so that model forms (Django admin) display the error on the field instead of failing in `save()`.

        Raises:
            ValidationError: If the pins_configuration does not conform to the schema.
        """
        super().clean()
        # None means the form has already reported the field as missing or malformed.
        if self.pins_configuration is not None:
            jsonschema_validation(self.pins_configuration, settings.DATASHEET_JSON_SCHEMA, "pins_configuration")

    def save(self, *args, **kwargs) -> None:
        """
        Override the save method to validate the pins_configuration JSON field against
        the DATASHEET_JSON_SCHEMA defined in settings before saving the instance.

        Raises:
            ValidationError: If the pins_configuration does not conform to the schema.
        """
        jsonschema_validation(self.pins_configuration, settings.DATASHEET_JSON_SCHEMA, "pins_configuration")
        super().save(*args, **kwargs)


class Device(NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
    """

    AVAILABLE_COMM_PROTOCOLS = (("USB", "USB"),)

    category = models.ForeignKey(
        DeviceCategory,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="device category",
    )
    # null=True: an unknown uid is NULL, not "", so several devices without uid do not break `unique`.
    uid = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        verbose_name="device uid",
        help_text="Unique device card UID (e.g: '12AB34567890DEAD').",
    )
    communication_protocol = models.CharField(
        max_length=16,
        choices=AVAILABLE_COMM_PROTOCOLS,
        verbose_name="communication protocol",
        help_text="Communication protocol used by this device.",
    )
    path = models.CharField(
        max_length=64,
        blank=True,
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

    class Meta:
        verbose_name = "device"
        verbose_name_plural = "devices"

    def __str__(self) -> str:
        return f"Device `{self.name}` : {self.uid} : {self.path}"

    def save(self, *args, **kwargs) -> None:
        adding = self._state.adding  # Read before create Device with super().save()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if adding:
                self._create_pins_with_datasheet()

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

    @transaction.atomic
    def _create_pins_with_datasheet(self) -> None:
        """
        Create the pins of the device from the datasheet of its category (`pins_configuration`).

        A pin is created for each pin number found in the datasheet. Its `channels_available` are the channels
        whose configuration lists this pin number. `channel_choiced` is left empty: it is chosen later.
        A pin that already exists for this device is reused and only gets its `channels_available` refreshed,
        so the method can run again. A pin missing from the datasheet is neither deleted nor changed.

        The device must already be saved. The datasheet is trusted: `DeviceCategory.save()` validates it.
        Everything runs in one transaction, so nothing is written if the method raises.

        Raises:
            Channel.DoesNotExist: If a channel of `available_channels` is not in the database
                (channels are created by the seeder, never by this method).
        """
        # Models are fetched by name because `pin.py` imports this module: importing them here would be circular.
        # The type checker only knows them as `Model`, so the code below handles primary keys, not instances.
        Pin = apps.get_model("hardware", "Pin")
        Channel = apps.get_model("hardware", "Channel")
        PinChannelsAvailableRelationship = apps.get_model("hardware", "Pin_channels_available")

        pins_cfg = self.category.pins_configuration
        channel_names: list[str] = pins_cfg.get("available_channels") or []

        # {channel name: channel pk}
        channel_ids: dict[str, int] = dict(Channel.objects.filter(name__in=channel_names).values_list("name", "pk"))
        # Channels belong to the seeder: a missing name is a datasheet or seeding error, not a channel to create.
        if missing_channel_names := set(channel_names) - channel_ids.keys():
            raise Channel.DoesNotExist(
                f"{self.category}: channels not found in database {sorted(missing_channel_names)}"
            )

        # {pin number: {pk of each channel available on this pin}}
        pins_with_chan: dict[int, set[int]] = {}
        for channel_name, channel_id in channel_ids.items():
            # The datasheet key is the plural of the channel name, e.g. digit -> digits.
            # TODO: warn the user when a channel of `available_channels` has no key in the datasheet.
            for chan_config in pins_cfg.get(f"{channel_name}s") or []:
                for pin_num in chan_config.get("pins") or []:
                    pins_with_chan.setdefault(pin_num, set()).add(channel_id)

        # {pin number: pin pk}: the pins already created for this device are reused, the others are created.
        pin_ids: dict[int, int] = dict(Pin.objects.filter(device=self).values_list("pin_number", "pk"))
        new_pin_numbers = sorted(pins_with_chan.keys() - pin_ids.keys())
        new_pins = Pin.objects.bulk_create([Pin(device=self, pin_number=number) for number in new_pin_numbers])
        pin_ids.update(zip(new_pin_numbers, (new_pin.pk for new_pin in new_pins)))

        # `Pin.channels_available` is a ManyToMany field and `bulk_create` does not fill it: the links are written
        # in its intermediate table. The old links of the pins are erased first, so a second run gives the same result.
        PinChannelsAvailableRelationship.objects.filter(
            pin_id__in=[pin_ids[number] for number in pins_with_chan]
        ).delete()
        PinChannelsAvailableRelationship.objects.bulk_create(
            [
                PinChannelsAvailableRelationship(pin_id=pin_ids[pin_number], channel_id=chan_pk)
                for pin_number, chan_pks in pins_with_chan.items()
                for chan_pk in chan_pks
            ]
        )
