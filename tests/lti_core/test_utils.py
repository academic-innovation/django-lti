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
