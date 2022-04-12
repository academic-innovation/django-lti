from datetime import timedelta
from typing import Any, Optional

import django.utils.timezone as tz
from django.core.management.base import BaseCommand, CommandParser
from django.db import DatabaseError, transaction
from django.template.defaultfilters import pluralize

from lti_tool.models import Key


class Command(BaseCommand):
    help = "Creates a new keypair and deactivates old ones."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--deactivate-after",
            type=int,
            default=7,
            help="The age in days beyond which keys should be deactivated.",
        )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        now = tz.now()
        days = timedelta(days=options["deactivate_after"])
        try:
            with transaction.atomic():
                new_key = Key.objects.generate()
                deactivated = (
                    Key.objects.active()
                    .filter(datetime_created__lt=now - days)
                    .update(is_active=False)
                )
            self.stdout.write(self.style.SUCCESS(f"Created new key {new_key}."))
            if deactivated > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deactivated {deactivated} key{pluralize(deactivated)}."
                    )
                )
        except DatabaseError:
            self.stdout.write(self.style.ERROR("Unable to rotate keys."))
