"""
Centralized definition of the version number for the GardenIQ Backend project.
Follows the Semantic Versioning format (MAJOR.MINOR.PATCH)
"""

from functools import total_ordering

from django.core.validators import RegexValidator

import requests

from gardeniq.hardware.protocols.settings import pattern_strict_version
from gardeniq.settings import get_config_value

MAJOR = 1
MINOR = 0
PATCH = 0

__version__ = f"{MAJOR}.{MINOR}.{PATCH}"


@total_ordering
class Version:
    """
    A class representing a semantic version number (major.minor.patch).

    This class parses and compares version strings following the semantic versioning format.
    It supports equality and less-than comparisons between Version objects.

    Args:
        version_str (str): A version string in the format "major.minor.patch" (e.g., "1.2.3").
        run_validator (bool, optional): Whether to validate the version string format using
            a regex validator. Defaults to True.

    Attributes:
        major (int): The major version number.
        minor (int): The minor version number.
        patch (int): The patch version number.

    Raises:
        ValidationError: If run_validator is True and version_str doesn't match the expected format.
        ValueError: If version string components cannot be converted to integers.

    Examples:
        >>> v1 = Version("1.2.3")
        >>> v2 = Version("1.2.4")
        >>> v1 < v2
        True
        >>> v1 == Version("1.2.3")
        True
        >>> str(v1)
        'Version 1.2.3'
    """

    def __init__(self, version_str: str, run_validator: bool = True) -> None:
        if run_validator:
            validator = RegexValidator(pattern_strict_version)
            validator(version_str)
        self.major, self.minor, self.patch = [int(v) for v in version_str.split(".")]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Version):
            raise NotImplementedError
        return self.major == value.major and self.minor == value.minor and self.patch == value.patch

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Version):
            raise NotImplementedError
        if self.major != value.major:
            return self.major < value.major
        if self.minor != value.minor:
            return self.minor < value.minor
        return self.patch < value.patch

    def __repr__(self) -> str:
        return f"Version {self.major}.{self.minor}.{self.patch}"


def request_repot_version(repot_url: str) -> str:
    """
    Fetches the latest release version from a GitHub repository.

    Args:
        repot_url (str): The base URL of the GitHub repository
                         (e.g., 'https://api.github.com/repos/owner/repo')

    Returns:
        str: The latest version string with 'v' prefix removed if present.
             Returns an empty string if the request fails or encounters an error.

    Raises:
        None: Errors are silently handled and return an empty string.

    Note:
        - Appends '/releases/latest' to the provided repository URL
        - Strips 'v' prefix from version tags (e.g., 'v1.0.0' becomes '1.0.0')
        - Returns empty string on HTTP errors (should be logged in future implementation)
    """
    suffix_url = "/releases/latest"
    url = repot_url + suffix_url
    response = requests.get(url)
    if response.status_code == 200:
        res_data = response.json()
        latest_version: str = res_data["tag_name"]
        if "v" in latest_version:
            return latest_version.replace("v", "")
        else:
            return latest_version
    else:
        # TODO: register error to logs system
        #   log status_code and response.json()
        return "0.0.0"


def get_micropython_version() -> str:
    base_url = get_config_value("micropython_repot", default="", cast=str)
    return request_repot_version(base_url)


def get_gd_fw_version() -> str:
    base_url = get_config_value("gardeniq_firmware_repot", default="", cast=str)
    return request_repot_version(base_url)


micropython_version = get_micropython_version()
garden_firmware_version = get_gd_fw_version()
