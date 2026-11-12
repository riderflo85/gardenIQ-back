import pytest

from gardeniq.hardware.fixtures.seeders.channel import ChannelSeeder
from gardeniq.hardware.models import Channel
from gardeniq.hardware.serializers import ChannelSeederSerializer


@pytest.mark.django_db
class TestChannelSeeder:

    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def channel_seeder(self, success_logs, error_logs):
        return ChannelSeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    def test_seeder_attributes(self, channel_seeder):
        """The seeder targets Channel and its source file exists."""
        # WHEN / THEN
        assert channel_seeder.model is Channel
        assert channel_seeder.serializer is ChannelSeederSerializer
        assert channel_seeder.filename == "channels.json"
        assert channel_seeder.source_file.exists()

    def test_seed_creates_channels_when_db_is_empty(self, channel_seeder, success_logs):
        """Seeding an empty database creates the six channels, only digit, analog and pwm being ready."""
        # GIVEN
        assert Channel.objects.count() == 0

        # WHEN
        channel_seeder.seed()

        # THEN
        assert len(success_logs) == 6
        assert dict(Channel.objects.order_by("seed_id").values_list("name", "is_ready")) == {
            "digit": True,
            "analog": True,
            "pwm": True,
            "i2c": False,
            "spi": False,
            "uart": False,
        }

    def test_seed_skips_when_entries_already_exist(self, channel_seeder, error_logs):
        """A second seed without authorize_update does not create duplicates."""
        # GIVEN
        channel_seeder.seed()

        # WHEN
        channel_seeder.seed()

        # THEN
        assert Channel.objects.count() == 6
        assert len(error_logs) == 1

    def test_seed_updates_entry_when_authorize_update_is_true(self, channel_seeder):
        """seed(authorize_update=True) restores the source data of an existing entry."""
        # GIVEN
        channel_seeder.seed()
        Channel.objects.filter(seed_id=1).update(name="Old name", is_ready=False)

        # WHEN
        channel_seeder.seed(authorize_update=True)

        # THEN
        channel = Channel.objects.get(seed_id=1)
        assert Channel.objects.count() == 6
        assert channel.name == "digit"
        assert channel.is_ready is True
