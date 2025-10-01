import re


def normalize_role(role: str) -> str:
    """Expands a simple context role to a full URI, if needed."""
    if re.match(r"^\w+$", role):
        return f"http://purl.imsglobal.org/vocab/lis/v2/membership#{role}"
    return role
