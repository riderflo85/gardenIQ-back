from typing import Literal

from serial.tools.list_ports import comports

from gardeniq.settings.project.cards import ListDevicesFormat

# For typing
LDFormats = Literal[
    ListDevicesFormat.STR,
    ListDevicesFormat.LIST_DEVICES,
    ListDevicesFormat.LIST_NAMES,
]


def list_connected_devices(ret_type: LDFormats, verbose: bool = False) -> str | list:
    """Get the connected USB devices.

    Args:
        ret_type (LDFormats): Type of data formating.
        verbose (bool, optional): Return more device informations. Defaults to False.

    Returns:
        str | list: String or List to device(s) informations.
    """
    devices = comports()

    match ret_type:
        case ListDevicesFormat.STR:
            devices_string_informations = ""

            for device in devices:
                if not verbose:
                    devices_string_informations = f"{devices_string_informations}\n{device.name}"
                    continue

                more_infos = [
                    f"hwid: {device.hwid}",
                    f"product: {device.product}",
                    f"desc: {device.description}",
                    f"location: {device.location}",
                    f"interface: {device.interface}",
                    f"manufacturer: {device.manufacturer}",
                ]
                more_infos_stringify = "\n\t" + "\n\t".join(more_infos)
                devices_string_informations = f"{devices_string_informations}\n{device.device}{more_infos_stringify}\n"

            return devices_string_informations

        case ListDevicesFormat.LIST_DEVICES:
            return [device.device for device in devices]

        case ListDevicesFormat.LIST_NAMES:
            return [device.name for device in devices]

        case _:
            return devices
