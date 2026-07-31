from typing import List
from typing import Tuple

import pytest

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.base.fixtures.seeders import SeedersManager
from gardeniq.base.fixtures.seeders import StatusSeeder
from gardeniq.base.models import Status


class TestManager:
    fake_seeders_attrs = [
        ("FooSeeder", ["TotoSeeder"]),
        ("BlaSeeder", []),
        ("BazSeeder", ["LoremSeeder"]),
        ("LoremSeeder", ["FooSeeder", "BlaSeeder"]),
        ("TotoSeeder", []),
    ]

    @pytest.fixture
    def fake_seeder(self, mocker):
        def _make_fake_seeder(seeders_attrs: List[Tuple[str, List[str]]]) -> List[object]:
            """Make a fake seeder with dependencies.

            Args:
                seeders_attrs (List[Tuple[str,List[str]]]): List of name and dependencies attributs for seeders.
                    ex: [
                            (
                                "SeederName", # Name class
                                ["FooSeeder"] # Dependencies class
                            ),
                        ]

            Returns:
                List[object]: return fake seeders class.
            """
            fakes_cls = []
            for seed in seeders_attrs:
                cls_name, cls_dep = seed
                new_fake_cls = mocker.Mock()
                new_fake_cls.__name__ = cls_name
                # If .__repr__ is not surcharged, print(new_fake_cls) return the <Mock id="xxxxx">. :(
                new_fake_cls.__repr__ = lambda cls: f"<Mock name={cls.__name__}"
                new_fake_cls.dependencies = cls_dep
                fakes_cls.append(new_fake_cls)
            return fakes_cls

        return _make_fake_seeder

    def test_import_seeders_with_all_apps(self):
        # GIVEN
        expected_seeders_name = [
            "StatusSeeder",
            "OrderSeeder",
        ]

        # WHEN
        seeds_manager = SeedersManager()
        seeds_manager.collect_all()

        # THEN
        seeders_name = []
        for seeder_klass in seeds_manager.seeders_cls:
            assert issubclass(seeder_klass, BaseSeeder)
            seeders_name.append(seeder_klass.__name__)
        assert seeders_name == expected_seeders_name

    @pytest.mark.parametrize(
        "app_name, expected_seeders_name",
        [
            ("orderlg", ["OrderSeeder"]),
            ("base", ["StatusSeeder"]),
        ],
    )
    def test_import_seeders_with_app_name(self, app_name, expected_seeders_name):
        # GIVEN
        # WHEN
        seeds_manager = SeedersManager()
        seeds_manager.collect_by_app(app_name)

        # THEN
        assert [s.__name__ for s in seeds_manager.seeders_cls] == expected_seeders_name

    def test_graph_dependencies(self, fake_seeder):
        # GiVEN
        fake_seeders_obj = fake_seeder(self.fake_seeders_attrs)
        FooSeeder, BlaSeeder, BazSeeder, LoremSeeder, TotoSeeder = fake_seeders_obj

        expected = {
            FooSeeder: [TotoSeeder],
            BlaSeeder: [],
            BazSeeder: [LoremSeeder],
            LoremSeeder: [FooSeeder, BlaSeeder],
            TotoSeeder: [],
        }

        # WHEN
        seeds_manager = SeedersManager()
        graph_seeders = seeds_manager.build_seeder_graph(fake_seeders_obj)

        # THEN
        assert graph_seeders == expected

    def test_sorted_seeders_by_dependencies(self, fake_seeder):
        # GIVEN
        fake_seeders_obj = fake_seeder(self.fake_seeders_attrs)
        FooSeeder, BlaSeeder, BazSeeder, LoremSeeder, TotoSeeder = fake_seeders_obj

        expected = [
            BlaSeeder,
            TotoSeeder,
            FooSeeder,
            LoremSeeder,
            BazSeeder,
        ]

        # WHEN
        seeds_manager = SeedersManager()
        sorted_seeders = seeds_manager.topological_sort(fake_seeders_obj)

        # THEN
        assert sorted_seeders == expected


@pytest.mark.django_db
class TestStatusSeeder:
    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def status_seeder(self, success_logs, error_logs):
        return StatusSeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    def test_seed_creates_all_entries_when_db_is_empty(self, status_seeder, success_logs):
        # GIVEN
        assert Status.objects.count() == 0

        # WHEN
        status_seeder.seed()

        # THEN
        assert Status.objects.count() == 2
        assert len(success_logs) == 2

    def test_seed_skips_creation_when_entries_already_exist(self, status_seeder, error_logs):
        # GIVEN
        Status.objects.create(name="Existing", tag="existing")

        # WHEN
        status_seeder.seed()

        # THEN
        assert Status.objects.count() == 1
        assert len(error_logs) == 1

    def test_seed_updates_entries_when_authorize_update_is_true(self, status_seeder, success_logs):
        # GIVEN — name/tag must match source file for search_field_name lookup
        Status.objects.create(seed_id=1, name="En ligne", color="#000000", tag="device")
        Status.objects.create(seed_id=2, name="Hors ligne", color="#000000", tag="device")

        # WHEN
        status_seeder.seed(authorize_update=True)

        # THEN
        assert Status.objects.count() == 2
        updated_status = Status.objects.get(seed_id=1)
        assert updated_status.color == "#90EE90"
        assert len(success_logs) == 2

    def test_seed_creates_missing_entry_during_update(self, status_seeder, success_logs):
        # GIVEN — only seed_id=1 exists; seed_id=2 must be created during update
        Status.objects.create(seed_id=1, name="En ligne", color="#90EE90", tag="device")

        # WHEN
        status_seeder.seed(authorize_update=True)

        # THEN
        assert Status.objects.count() == 2
        assert Status.objects.filter(seed_id=2).exists()

    def test_create_entries(self, status_seeder, success_logs):
        # GIVEN
        data = [{"seed_id": 10, "is_ready": True, "name": "Test Status", "color": "#FFFFFF", "tag": "test"}]

        # WHEN
        status_seeder._create_entries(data)

        # THEN
        assert Status.objects.count() == 1
        assert len(success_logs) == 1

    def test_update_existing_entry(self, status_seeder, success_logs):
        # GIVEN — name/tag must match search_field_name; only color changes
        Status.objects.create(seed_id=10, name="Test Status", color="#000000", tag="test")
        data = [{"seed_id": 10, "is_ready": True, "name": "Test Status", "color": "#FFFFFF", "tag": "test"}]

        # WHEN
        status_seeder._update_entries(data)

        # THEN
        assert Status.objects.count() == 1
        updated = Status.objects.get(seed_id=10)
        assert updated.color == "#FFFFFF"
        assert len(success_logs) == 1

    def test_update_creates_entry_if_not_found(self, status_seeder, success_logs):
        # GIVEN
        data = [{"seed_id": 99, "is_ready": True, "name": "Missing Status", "color": "#AAAAAA", "tag": "missing"}]

        # WHEN
        status_seeder._update_entries(data)

        # THEN
        assert Status.objects.count() == 1
        assert Status.objects.filter(seed_id=99).exists()
        assert len(success_logs) == 1
