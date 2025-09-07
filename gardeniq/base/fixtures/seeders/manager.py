from collections import defaultdict
from importlib import import_module
from typing import Dict
from typing import List

from django.apps import apps
from django.conf import settings


class SeedersManager:

    def __init__(self):
        self.seeders_cls = []

    @staticmethod
    def _build_potential_seeder_name(app_name: str, container: List) -> None:
        """Build the potential seeder name with app name string.
        Append result to container.
        """
        for model_obj in apps.get_app_config(app_name).get_models():
            model_name = model_obj._meta.model_name
            # model_name is str or None
            if model_name:
                potential_seeder = f"{model_name.title()}Seeder"
                container.append(potential_seeder)

    def _import_seeders_module(self, app_name: str, potential_seeders: List[str]) -> bool:
        """Try import seeders module by app.
        If app has not seeders module ignore.
        Else register seeders class in `seeder_cls` attribut.
        """
        try:
            module_obj = import_module(f"gardeniq.{app_name}.{settings.SEEDERS_DIR}")
        except ModuleNotFoundError:
            return False
        for p_seeder_name in potential_seeders:
            seeder_klass = getattr(module_obj, p_seeder_name, False)
            if seeder_klass:
                self.seeders_cls.append(seeder_klass)
        return True

    def collect_all(self) -> None:
        """Collect all seeders classes.
        The collect is based on `LOCAL_APPS` setting.
        """
        # Is a List[str] -> ['gardeniq.app_name']
        local_apps_name = settings.LOCAL_APPS
        # Get only app name without 'gardeniq.' string
        local_apps_name = [app_n.split(".")[-1] for app_n in local_apps_name]

        # apps_potential_seeders is a dict with all potential seeders classes name in all apps.
        apps_potential_seeders = defaultdict(list)
        for local_app_str in local_apps_name:
            self._build_potential_seeder_name(
                app_name=local_app_str,
                container=apps_potential_seeders[local_app_str],
            )

        for app_name, potential_seeders in apps_potential_seeders.items():
            # if result of method is not True that is seeder does not exist.
            if not self._import_seeders_module(app_name, potential_seeders):
                continue

    def collect_by_app(self, app_name: str) -> None:
        """Collect all seeders classes inside a app.
        The collect is based on `app_name` parameter.
        """
        potential_seeders: List[str] = []
        self._build_potential_seeder_name(
            app_name=app_name,
            container=potential_seeders,
        )
        self._import_seeders_module(app_name, potential_seeders)

    def build_seeder_graph(self, seed_classes: List) -> Dict:
        """Build the graph dependencies seeders."""
        graph = defaultdict(list)
        name_to_class = {kls.__name__: kls for kls in seed_classes}

        for klass in seed_classes:
            graph[klass]
            for dep in klass.dependencies:
                graph[klass].append(name_to_class[dep])

        return graph

    def togological_sort(self, seed_classes: List) -> List:
        """Sort seeders classes with topological logic based on dependencies seeds."""
        graph = self.build_seeder_graph(seed_classes)
        visited = set()
        tmp = set()
        result = []

        def visit(seeder):
            if seeder not in visited:
                tmp.add(seeder)
                for dep in graph[seeder]:
                    visit(dep)
                visited.add(seeder)
                tmp.remove(seeder)

        for klass in seed_classes:
            if klass not in visited:
                visit(klass)

        result = list(visited)
        tmp.clear()
        visited.clear()
        return result
