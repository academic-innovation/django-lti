from django.contrib import auth
from django.contrib.auth import load_backend
from django.core.exceptions import ImproperlyConfigured

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from lti_tool.auth.backends import LtiLaunchAuthenticationBackend


class LtiLaunchAuthenticationMiddleware:
    """Middleware for utilizing LMS-provided authentication via LTI launch.

    This middleware works in conjunction with `LtiLaunchMiddleware`.  The
    `LtiLaunchMiddleware` MUST appear before this middleware in the middleware list.

    If request.user is not authenticated, then this middleware attempts to
    authenticate the username from ``request.lti_launch.user.sub``.

    If authentication is successful, the user is automatically logged in to
    persist the user in the session.

    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        if get_response is None:
            raise ValueError("get_response must be provided.")
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)
        if self.is_async:
            markcoroutinefunction(self)
        super().__init__()

    force_logout_if_no_launch = True

    def __call__(self, request):
        if self.is_async:
            return self.__acall__(request)
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "lti_launch"):
            raise ImproperlyConfigured(
                "The Django LTI launch auth middleware requires the"
                " LTI launch middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'lti_tool.auth.LtiLaunchMiddleware'"
                " before the LtiLaunchAuthenticationMiddleware class."
            )
        try:
            username = request.lti_launch.user.sub
        except AttributeError:
            # If the LTI launch user doesn't exist then remove any existing
            # authenticated remote-user, or return (leaving request.user set to
            # AnonymousUser by the AuthenticationMiddleware).
            if self.force_logout_if_no_launch and request.user.is_authenticated:
                self._remove_invalid_user(request)
            return self.get_response(request)
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if request.user.get_username() == self.clean_username(username, request):
                return self.get_response(request)
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
        return self.get_response(request)

    async def __acall__(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "lti_launch"):
            raise ImproperlyConfigured(
                "The Django LTI launch auth middleware requires the"
                " LTI launch middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'lti_tool.auth.LtiLaunchMiddleware'"
                " before the LtiLaunchAuthenticationMiddleware class."
            )
        try:
            username = request.lti_launch.user.sub
        except AttributeError:
            # If the LTI launch user doesn't exist then remove any existing
            # authenticated remote-user, or return (leaving request.user set to
            # AnonymousUser by the AuthenticationMiddleware).
            if self.force_logout_if_no_launch:
                user = await request.auser()
                if user.is_authenticated:
                    await self._aremove_invalid_user(request)
            return await self.get_response(request)
        user = await request.auser()
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if user.is_authenticated:
            if user.get_username() == self.clean_username(username, request):
                return await self.get_response(request)
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                await self._aremove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = await auth.aauthenticate(request, lti_launch_user_id=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            await auth.alogin(request, user)

        return await self.get_response(request)

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

    async def _aremove_invalid_user(self, request):
        # Remove the current authenticated user in the request which is invalid
        # but only if the user is authenticated via the LtiLaunchAuthenticationBackend.
        try:
            stored_backend = load_backend(
                await request.session.aget(auth.BACKEND_SESSION_KEY, "")
            )
        except ImportError:
            # Backend failed to load.
            await auth.alogout(request)
        else:
            if isinstance(stored_backend, LtiLaunchAuthenticationBackend):
                await auth.alogout(request)


class PersistentLtiLaunchAuthenticationMiddleware(LtiLaunchAuthenticationMiddleware):
    """Middleware for web-server provided authentication on logon pages.

    Like LtiLaunchAuthenticationMiddleware but keeps the user authenticated even if
    the ``request.META`` key is not found in the request. Useful for
    setups when the external authentication is only expected to happen
    on some "logon" URL and the rest of the application wants to use
    Django's authentication mechanism.
    """

    force_logout_if_no_launch = False
