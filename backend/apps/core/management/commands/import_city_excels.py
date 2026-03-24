from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.destinations.importers import import_excel_directory


class Command(BaseCommand):
    help = "Import Chinese travel city Excel files into MySQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            type=str,
            default=r"C:/Users/YT-yuntian/Desktop/cities_data_excel",
            help="Directory containing city Excel files.",
        )
        parser.add_argument("--overwrite", action="store_true", help="Delete attractions missing from the current workbook.")
        parser.add_argument("--limit", type=int, default=None, help="Only import the first N files.")

    def handle(self, *args, **options):
        directory = Path(options["directory"])
        if not directory.exists():
            raise CommandError(f"Directory not found: {directory}")

        cities = import_excel_directory(directory, overwrite=options["overwrite"], limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(f"Imported {len(cities)} city workbooks from {directory}"))
