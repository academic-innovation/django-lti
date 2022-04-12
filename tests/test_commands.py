from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.utils.timezone import now

import pytest

from lti_tool.models import Key


@pytest.mark.django_db
def test_rotate_keys():
    Key.objects.create(
        public_key="", private_key="", datetime_created=now() - timedelta(days=1)
    )
    Key.objects.create(
        public_key="", private_key="", datetime_created=now() - timedelta(days=3)
    )
    out = StringIO()
    call_command("rotate_keys", "--deactivate-after=2", stdout=out)
    assert "Created new key" in out.getvalue()
    assert "Deactivated 1 key." in out.getvalue()
    assert Key.objects.count() == 3
    assert Key.objects.active().count() == 2
