import hmac
import re
from base64 import b64encode


def normalize_role(role: str) -> str:
    """Expands a simple context role to a full URI, if needed."""
    if re.match(r"^\w+$", role):
        return f"http://purl.imsglobal.org/vocab/lis/v2/membership#{role}"
    return role


def validate_migration_claim(launch_data: dict, oauth_secret: str) -> bool:
    """Verifies a signature passed in the LTI 1.1 migration claim."""
    try:
        migration_claim = launch_data[
            "https://purl.imsglobal.org/spec/lti/claim/lti1p1"
        ]
        oauth_consumer_key = migration_claim["oauth_consumer_key"]
        oauth_consumer_key_sign = migration_claim["oauth_consumer_key_sign"]
    except KeyError:
        return False
    base_string = "&".join(
        [
            oauth_consumer_key,
            launch_data["https://purl.imsglobal.org/spec/lti/claim/deployment_id"],
            launch_data["iss"],
            launch_data["aud"],
            str(launch_data["exp"]),
            launch_data["nonce"],
        ]
    )
    signed_base_string = hmac.digest(
        oauth_secret.encode(), base_string.encode(), "sha256"
    )
    computed_signature = b64encode(signed_base_string).decode()
    return oauth_consumer_key_sign == computed_signature
