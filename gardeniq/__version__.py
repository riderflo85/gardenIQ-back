"""
Centralized definition of the version number for the GardenIQ Backend project.
Follows the Semantic Versioning format (MAJOR.MINOR.PATCH)
"""
import requests

from gardeniq.settings import get_config_value

MAJOR = 1
MINOR = 0
PATCH = 0

__version__ = f"{MAJOR}.{MINOR}.{PATCH}"


def get_micropython_version() -> str:
    """
    Fetches the latest MicroPython version from the configured repository.

    Returns:
        str: The latest MicroPython version string without the leading 'v' if present.
             Returns an empty string if the request fails or the version cannot be determined.

    Notes:
        - The base URL for the repository is retrieved from the configuration using the key 'micropython_repot'.
        - If the HTTP request fails, an empty string is returned and an error should be logged (TODO).
    """
    suffix_url = "/releases/latest"
    base_url = get_config_value("micropython_repot", default="", cast=str)
    url = base_url + suffix_url
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
        return ""


micropython_version = get_micropython_version()
