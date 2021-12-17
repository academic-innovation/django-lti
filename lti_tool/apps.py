from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LtiToolAppConfig(AppConfig):
    """LTI tool app configuration."""

    name = "lti_tool"
    verbose_name = _("LTI tool")
