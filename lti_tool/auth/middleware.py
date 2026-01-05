from django.conf import settings
from django.contrib import auth
from django.contrib.auth import load_backend
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin

from lti_tool.auth.backends import LtiLaunchAuthenticationBackend
from lti_tool.models import LtiUser


class LtiLaunchAuthenticationMiddleware(MiddlewareMixin):
    """Middleware for utilizing LMS-provided authentication via LTI launch.

    This middleware works in conjunction with `LtiLaunchMiddleware` and
    Django's `AuthenticationMiddleware`.  The `LtiLaunchMiddleware` and
    `AuthenticationMiddleware` MUST appear before this middleware in the
    middleware list.

    If request.user is not authenticated, then this middleware attempts to
    authenticate the username from ``request.lti_launch.user.sub``.

    If authentication is successful, the user is automatically logged in to
    persist the user in the session.

    """

    force_logout_if_no_launch = True

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django LTI launch auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the LtiLaunchAuthenticationMiddleware class."
            )
        # LtiLaunchMiddleware is required so that request.lti_launch exists.
        if not hasattr(request, "lti_launch"):
            raise ImproperlyConfigured(
                "The Django LTI launch auth middleware requires the"
                " LTI launch middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'lti_tool.auth.LtiLaunchMiddleware'"
                " before the LtiLaunchAuthenticationMiddleware class."
            )

        # If the request doesn't have an LTILaunch object, then we can't
        # authenticate the user.
        if request.lti_launch.is_absent:  # pragma: no cover
            if self.force_logout_if_no_launch and request.user.is_authenticated:
                self._remove_invalid_user(request)
            return
        try:
            username = self.get_username(request)
        except LtiUser.DoesNotExist:
            # If the LTI launch user doesn't exist then remove any existing
            # authenticated remote-user, or return (leaving request.user set to
            # AnonymousUser by the AuthenticationMiddleware).
            if self.force_logout_if_no_launch and request.user.is_authenticated:
                self._remove_invalid_user(request)
            return

        # If the user is already authenticated and that user is the user we are
        # getting passed in the LTI launch, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if request.user.get_username() == self.clean_username(username, request):
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, lti_launch_user_id=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

    def clean_username(self, username, request):
        # Allow the backend to clean the username, if the backend defines a
        # clean_username method.
        backend_str = request.session[auth.BACKEND_SESSION_KEY]
        backend = auth.load_backend(backend_str)
        try:
            username = backend.clean_username(username)
        except AttributeError:  # Backend has no clean_username method.
            pass
        return username

    def get_username(self, request):
        """Get the username from the request.

        This method returns the value that will be used as the username of
        the Django user object. By default, this is the value of the
        `sub` attribute of the LTI user object.
        """
        if hasattr(settings, "LTI_TOOL") and settings.LTI_TOOL.get(
            "use_person_sourcedid", False
        ):
            username = request.lti_launch.get_claim(
                "https://purl.imsglobal.org/spec/lti/claim/lis"
            ).get("person_sourcedid")
        else:
            username = request.lti_launch.user.sub

        return username

    def _remove_invalid_user(self, request):
        # Remove the current authenticated user in the request which is invalid
        # but only if the user is authenticated via the LtiLaunchAuthenticationBackend.

        try:
            stored_backend = load_backend(
                request.session.get(auth.BACKEND_SESSION_KEY, "")
            )
        except ImportError:
            # backend failed to load
            auth.logout(request)
        else:
            if isinstance(stored_backend, LtiLaunchAuthenticationBackend):
                auth.logout(request)


class PersistentLtiLaunchAuthenticationMiddleware(LtiLaunchAuthenticationMiddleware):
    """Middleware for web-server provided authentication on logon pages.

    Like LtiLaunchAuthenticationMiddleware but keeps the user authenticated even if
    the ``request.META`` key is not found in the request. Useful for
    setups when the external authentication is only expected to happen
    on some "logon" URL and the rest of the application wants to use
    Django's authentication mechanism.
    """

    force_logout_if_no_launch = False
