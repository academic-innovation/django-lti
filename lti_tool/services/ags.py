from django.utils.dateparse import parse_datetime
from pylti1p3.assignments_grades import AssignmentsGradesService
from pylti1p3.lineitem import LineItem
from pylti1p3.service_connector import ServiceConnector

from ..constants import AgsScope
from ..models import LtiContext, LtiLineItem


def context_to_ags_definition(context: LtiContext) -> dict:
    scope_pairs = [
        ("can_query_lineitems", AgsScope.QUERY_LINEITEMS),
        ("can_manage_lineitems", AgsScope.MANAGE_LINEITEMS),
        ("can_publish_scores", AgsScope.PUBLISH_SCORES),
        ("can_access_results", AgsScope.ACCESS_RESULTS),
    ]

    return {
        "scope": [s for f, s in scope_pairs if getattr(context, f)],
        "lineitems": context.lineitems_url,
    }


def service_for_context(context: LtiContext) -> AssignmentsGradesService:
    connector = ServiceConnector(context.deployment.registration.to_registration())
    return AssignmentsGradesService(connector, context_to_ags_definition(context))


def sync_line_item(context: LtiContext, line_item: LineItem) -> LtiLineItem:
    start_date_time = parse_datetime(line_item.get_start_date_time() or "")
    end_date_time = parse_datetime(line_item.get_end_date_time() or "")

    lti_line_item, _ = LtiLineItem.objects.update_or_create(
        context=context,
        url=line_item.get_id(),
        defaults=dict(
            maximum_score=line_item.get_score_maximum(),
            label=line_item.get_label(),
            tag=line_item.get_tag(),
            resource_id=line_item.get_resource_id(),
            start_datetime=start_date_time,
            end_datetime=end_date_time,
        ),
    )

    return lti_line_item


def sync_line_items(context: LtiContext, update_only: bool = True):
    """
    Fetches all line items from the Platform for `context` and updates the local
    instances to match.

    :param update_only: Only update existing items, ignoring items not in database.
    :type update_only: bool
    """
    service = service_for_context(context)
    existing_line_item_ids = set(
        LtiLineItem.objects.filter(context=context).values_list("url", flat=True)
    )
    all_line_items = service.get_lineitems()
    if update_only:
        all_line_items = [
            line_item
            for line_item in all_line_items
            if line_item.id in existing_line_item_ids
        ]

    for line_item in all_line_items:
        sync_line_item(context, line_item)
