import pytest

from lti_tool.lti_core import utils


@pytest.mark.parametrize(
    ("input", "output"),
    [
        ("Learner", "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"),
        (
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
        ),
        (
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Staff",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Staff",
        ),
    ],
)
def test_normalize_role(input, output):
    assert utils.normalize_role(input) == output


@pytest.mark.parametrize(
    ("secret", "result"), [("my-lti11-secret", True), ("bad", False)]
)
def test_validate_migration_claim(secret, result):
    launch_data = {
        "nonce": "172we8671fd8z",
        "iat": 1551290796,
        "exp": 1551290856,
        "iss": "https://lmsvendor.com",
        "aud": "PM48OJSfGDTAzAo",
        "sub": "3",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "689302",
        "https://purl.imsglobal.org/spec/lti/claim/lti1p1": {
            "user_id": "34212",
            "oauth_consumer_key": "179248902",
            "oauth_consumer_key_sign": "lWd54kFo5qU7xshAna6v8BwoBm6tmUjc6GTax6+12ps=",
        },
    }
    assert utils.validate_migration_claim(launch_data, secret) == result
