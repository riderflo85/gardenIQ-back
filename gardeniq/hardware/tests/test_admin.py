import pytest

from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import SensorCategory

VALID_PIN_INIT_CFG = '{"c": "Pin", "a": {"id": "@pin"}}'

ADMIN_CASES = [
    pytest.param(
        DeviceCategory,
        "devicecategory",
        {"name": "Bad card", "pins_configuration": '{"digits": []}', "is_ready": "on"},
        "pins_configuration",
        id="devicecategory",
    ),
    pytest.param(
        ControllerCategory,
        "controllercategory",
        {"name": "Bad relay", "pin_init_cfg": '{"c": "Pin", "a": {"id": 4}}', "is_ready": "on"},
        "pin_init_cfg",
        id="controllercategory",
    ),
    pytest.param(
        SensorCategory,
        "sensorcategory",
        {"name": "Bad sensor", "unity_value": "C", "pin_init_cfg": '{"c": "ADC", "a": {"id": 4}}', "is_ready": "on"},
        "pin_init_cfg",
        id="sensorcategory",
    ),
]


@pytest.mark.django_db
class TestJSONFieldsAdmin:

    @pytest.mark.parametrize("model, model_name, data, field", ADMIN_CASES)
    def test_add_with_invalid_json_shows_form_error(self, admin_client, model, model_name, data, field):
        """An invalid JSON field is reported in the admin form instead of raising a 500."""
        # GIVEN
        url = f"/admin/hardware/{model_name}/add/"

        # WHEN
        response = admin_client.post(url, data)

        # THEN
        assert response.status_code == 200
        errors = response.context["adminform"].form.errors
        assert list(errors) == [field]
        assert errors[field][0].startswith("Failed validation JSON schema")
        assert model.objects.count() == 0

    def test_add_with_valid_pin_init_cfg_creates_category(self, admin_client):
        """A valid pin_init_cfg is saved from the admin form."""
        # GIVEN
        data = {"name": "Relay", "pin_init_cfg": VALID_PIN_INIT_CFG, "is_ready": "on"}

        # WHEN
        response = admin_client.post("/admin/hardware/controllercategory/add/", data)

        # THEN
        assert response.status_code == 302
        assert ControllerCategory.objects.get(name="Relay").pin_init_cfg == {"c": "Pin", "a": {"id": "@pin"}}
