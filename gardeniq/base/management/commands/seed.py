from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from gardeniq.base.fixtures.seeders import SeedersManager


class Command(BaseCommand):
    help = "Seed the database with fixtures."
    default_choice = "all"

    def _get_local_app(self) -> set[str]:
        s_manager = SeedersManager()
        s_manager.collect_all()
        return s_manager.available_apps

    def success_logger(self, msg) -> None:
        self.stdout.write(self.style.SUCCESS(msg))

    def error_logger(self, msg) -> None:
        self.stdout.write(self.style.ERROR(msg))

    def add_arguments(self, parser: CommandParser) -> None:
        apps_choices = self._get_local_app()
        apps_choices.add(self.default_choice)
        parser.add_argument(
            "--app",
            choices=apps_choices,
            action="store",
            default=self.default_choice,
            help="App name to seed. Default to all apps.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing fixtures. Default to False.",
        )

    def handle(self, *args, **options):
        """
        Handle the command.

        This method collects all seeders classes from the project and executes their seed method.
        If the --app option is provided, it will collect seeders classes from the specified app.
        If the --update option is provided, it will update existing fixtures.
        """
        manager = SeedersManager()
        if options["app"] == self.default_choice:
            manager.collect_all()
        else:
            manager.collect_by_app(options["app"])

        seeders_klass = manager.topological_sort(manager.seeders_cls)
        for seeder_cls in seeders_klass:
            seeder = seeder_cls(self.success_logger, self.error_logger)
            seeder.seed(options["update"])
