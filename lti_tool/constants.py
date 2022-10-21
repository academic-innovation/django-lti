from enum import Enum

SESSION_KEY = "_lti_tool_launch_id"

CONTEXT_ROLE_PATTERN = "http://purl.imsglobal.org/vocab/lis/v2/membership#{}"


class ContextRole(str, Enum):
    ADMINISTRATOR = CONTEXT_ROLE_PATTERN.format("Administrator")
    CONTENT_DEVELOPER = CONTEXT_ROLE_PATTERN.format("ContentDeveloper")
    INSTRUCTOR = CONTEXT_ROLE_PATTERN.format("Instructor")
    LEARNER = CONTEXT_ROLE_PATTERN.format("Learner")
    MENTOR = CONTEXT_ROLE_PATTERN.format("Mentor")

    @property
    def short_name(self) -> str:
        """Return the short name of this role."""
        return self.value[len(CONTEXT_ROLE_PATTERN.format("")) :]

    @property
    def full_name(self) -> str:
        """Return the full name of this roles."""
        return self.value


class AgsScope(str, Enum):
    MANAGE_LINEITEMS = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
    QUERY_LINEITEMS = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
    PUBLISH_SCORES = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
    ACCESS_RESULTS = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
