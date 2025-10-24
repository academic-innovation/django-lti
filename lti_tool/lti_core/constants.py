from enum import Enum

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
        """Return the full name of this role."""
        return self.value


CONTEXT_TYPE_PATTERN = "http://purl.imsglobal.org/vocab/lis/v2/course#{}"


class ContextType(str, Enum):
    COURSE_TEMPLATE = CONTEXT_TYPE_PATTERN.format("CourseTemplate")
    COURSE_OFFERING = CONTEXT_TYPE_PATTERN.format("CourseOffering")
    COURSE_SECTION = CONTEXT_TYPE_PATTERN.format("CourseSection")
    GROUP = CONTEXT_TYPE_PATTERN.format("Group")

    @property
    def short_name(self) -> str:
        """Return the short name of this context."""
        return self.value[len(CONTEXT_TYPE_PATTERN.format("")) :]

    @property
    def full_name(self) -> str:
        """Return the full name of this context."""
        return self.value


SYSTEM_ROLE_PATTERN = "http://purl.imsglobal.org/vocab/lis/v2/system/person#{}"


class SystemRole(str, Enum):
    ADMINISTRATOR = SYSTEM_ROLE_PATTERN.format("Administrator")
    NONE = SYSTEM_ROLE_PATTERN.format("None")
    ACCOUNT_ADMIN = SYSTEM_ROLE_PATTERN.format("AccountAdmin")
    CREATOR = SYSTEM_ROLE_PATTERN.format("Creator")
    SYS_ADMIN = SYSTEM_ROLE_PATTERN.format("SysAdmin")
    SYS_SUPPORT = SYSTEM_ROLE_PATTERN.format("SysSupport")
    USER = SYSTEM_ROLE_PATTERN.format("User")

    @property
    def short_name(self) -> str:
        """Return the short name of this role."""
        return self.value[len(SYSTEM_ROLE_PATTERN.format("")) :]

    @property
    def full_name(self) -> str:
        """Return the full name of this roles."""
        return self.value


INSTITUTION_ROLE_PATTERN = (
    "http://purl.imsglobal.org/vocab/lis/v2/institution/person#{}"
)


class InstitutionRole(str, Enum):
    ADMINISTRATOR = INSTITUTION_ROLE_PATTERN.format("Administrator")
    FACULTY = INSTITUTION_ROLE_PATTERN.format("Faculty")
    GUEST = INSTITUTION_ROLE_PATTERN.format("Guest")
    NONE = INSTITUTION_ROLE_PATTERN.format("None")
    OTHER = INSTITUTION_ROLE_PATTERN.format("Other")
    STAFF = INSTITUTION_ROLE_PATTERN.format("Staff")
    STUDENT = INSTITUTION_ROLE_PATTERN.format("Student")
    ALUMNI = INSTITUTION_ROLE_PATTERN.format("Alumni")
    INSTRUCTOR = INSTITUTION_ROLE_PATTERN.format("Instructor")
    LEARNER = INSTITUTION_ROLE_PATTERN.format("Learner")
    MEMBER = INSTITUTION_ROLE_PATTERN.format("Member")
    MENTOR = INSTITUTION_ROLE_PATTERN.format("Mentor")
    OBSERVER = INSTITUTION_ROLE_PATTERN.format("Observer")
    PROSPECTIVE_STUDENT = INSTITUTION_ROLE_PATTERN.format("ProspectiveStudent")

    @property
    def short_name(self) -> str:
        """Return the short name of this role."""
        return self.value[len(INSTITUTION_ROLE_PATTERN.format("")) :]

    @property
    def full_name(self) -> str:
        """Return the full name of this roles."""
        return self.value


class AgsScope(str, Enum):
    MANAGE_LINEITEMS = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
    QUERY_LINEITEMS = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
    PUBLISH_SCORES = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
    ACCESS_RESULTS = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
