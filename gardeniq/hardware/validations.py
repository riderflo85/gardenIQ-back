from django.core.exceptions import ValidationError

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate


def jsonschema_validation(instance: object, schema: dict, field_name_instance: str) -> None:
    """
    Validate a JSON instance againt a JSON schema and raise a Django ValidationError if validation fails.

    Args:
        instance (object): The JSON object/data to validate against the schema.
        schema (dict): The JSON schema dictionary to validate against.
        field_name_instance (str): The name of the field being validated, used in error messages.

    Returns:
        None: Returns nothing if the validation is successful.
    """
    try:
        validate(instance, schema)
    except JSONSchemaValidationError as e:
        message = f"Failed validation JSON schema : {e.message}. Path : {' -> '.join(str(p) for p in e.path)}"
        raise ValidationError({field_name_instance: message})
