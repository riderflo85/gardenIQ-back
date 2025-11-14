from typing import List
from typing import Tuple

import pytest

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.base.fixtures.seeders import SeedersManager


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
            "ArgumentSeeder",
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
            ("orderlg", ["ArgumentSeeder", "OrderSeeder"]),
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
