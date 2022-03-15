from typing import List

from pylti1p3.names_roles import NamesRolesProvisioningService
from pylti1p3.service_connector import ServiceConnector

from lti_tool.models import LtiContext


def fetch_member_data(context: LtiContext) -> List[dict]:
    """Fetches NRPS member data for the given context."""
    if not context.memberships_url:
        return []
    nrps = NamesRolesProvisioningService(
        ServiceConnector(context.deployment.registration.to_registration()),
        {"context_memberships_url": context.memberships_url},
    )
    return nrps.get_members()


def sync_memberships(context: LtiContext):
    """Fetches membership data using NRPS and updates context memberships."""
    member_data = fetch_member_data(context)
    context.update_memberships(member_data)
