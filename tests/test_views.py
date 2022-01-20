import json

import pytest

from lti_tool import models, views


@pytest.mark.django_db
def test_jwks(rf):
    models.Key.objects.generate()
    request = rf.get("/jwks.json")
    response = views.jwks(request)
    assert response.status_code == 200
    jwks = json.loads(response.content)
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
