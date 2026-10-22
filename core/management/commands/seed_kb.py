from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.rag import ingest


class Command(BaseCommand):
    help = "Ingest every PDF and TXT file in the knowledge-base seed directory."

    def handle(self, *args, **options):
        seed_directory = Path(settings.BASE_DIR) / "kb_seed"
        if not seed_directory.is_dir():
            raise CommandError(f"Seed directory does not exist: {seed_directory}")

        files = sorted(
            path for path in seed_directory.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pdf", ".txt"}
        )
        for path in files:
            try:
                count = ingest(path)
            except Exception as exc:
                raise CommandError(f"Could not ingest {path.name}: {exc}") from exc
            self.stdout.write(f"{path.name}: {count} chunks")
        if not files:
            self.stdout.write("No PDF or TXT files found in kb_seed.")
