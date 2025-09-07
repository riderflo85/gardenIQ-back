from os import environ
from typing import Any
from typing import Callable
from typing import Optional

from django.core.exceptions import ImproperlyConfigured

CONFIG_DEFAULT_NOT_SET = None


def get_config_value(
    name: str,
    default: Optional[Any] = CONFIG_DEFAULT_NOT_SET,
    cast: Optional[Callable[[Any], Any]] = None,
    missing_config_message_template: str = (
        'Unable to fetch "{config_name}" configuration, and no default value was provided.'
    ),
    casting_error_message_template: str = ('Unable to cast "{config_name}": {exception}'),
) -> Any:
    """Attempt to fetch the configuration values from different location, in that order:

    1. Environment variables
    2. Fallback to the default value

    Args:
        name (str): the name of the environment variable to fetch
        default (Optional[Any], optional): the default value to fallback to.
            Do not set the default to mark the config as required.
            Defaults to CONFIG_DEFAULT_NOT_SET.
        cast (Optional[Callable[[Any], Any]], optional): a callable function to format the raw value.
            Defaults to None.
        missing_config_message_template (str, optional): the error message to show when no configuration value could
            be retrieved and no default value was provied.
            Defaults to ( 'Unable to fecth "%(config_name)s" configuration, and no default value was provided.' ).
        casting_error_message_template (str, optional): the error message to shwo when trying
            to cast environment variable.
            Defaults to ( 'Unable to cast "{config_name}": {exception}' ).

    Raise:
        ImproperlyConfigured: when no configuration value could be retrieved and no default value was provided.
        ValueError: when there is a casting error.

    Returns:
        Any: the config value
    """
    value = environ.get(name.upper(), default)

    if value is CONFIG_DEFAULT_NOT_SET:
        raise ImproperlyConfigured(missing_config_message_template.format(config_name=name))

    if cast and value is not None:
        try:
            value = cast(value)
        except Exception as e:
            raise ValueError(casting_error_message_template.format(config_name=name, exception=e)) from e

    return value


def to_list(value: Optional[str], separator: Optional[str] = ",") -> list:
    """Cast the string value to list object.

    Args:
        value (Optional[str]): the source string.
        separator (Optional[str]): the separator to use.

    Returns:
        list: the casted value.
    """
    if not value:
        return []

    for char in ("[", "]"):
        if char in value:
            value = value.replace(char, "")

    return value.split(separator)


def to_bool(value: str) -> bool:
    """Cast the string value to bool object.

    Args:
        value (str): the source string.

    Returns:
        bool: the casted value.
    """
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        raise ValueError('The value "{}" is not valid.'.format(value))
