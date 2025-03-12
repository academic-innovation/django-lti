import warnings

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils.deprecation import RemovedInDjango50Warning
from django.utils.inspect import func_supports_parameter

from lti_tool.types import LtiLaunch

UserModel = get_user_model()


class LtiLaunchAuthenticationBackend(ModelBackend):
    """A Django authentication backend class for LTI launch authentication.

    This backend is to be used in conjunction with the
    ``LtiLaunchAuthenticationMiddleware`` found in the middleware module of
    this package, and is used when authentication is handled by an LMS and
    passed in via LTI launch.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, request, lti_launch_user_id):
        """Authenticate the user based on the LTI launch.

        The username passed as ``lti_launch_user_id`` is considered trusted. Return
        the ``User`` object with the given username. Create a new ``User``
        object if ``create_unknown_user`` is ``True``.

        Return None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
        if not lti_launch_user_id:
            return
        created = False
        user = None
        username = self.clean_username(lti_launch_user_id)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = UserModel._default_manager.get_or_create(
                **{UserModel.USERNAME_FIELD: username}
            )
        else:
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass

        # RemovedInDjango50Warning: When the deprecation ends, replace with:
        #   user = self.configure_user(request, user, created=created)
        if func_supports_parameter(self.configure_user, "created"):
            user = self.configure_user(request, user, created=created)
        else:
            warnings.warn(
                f"`created=True` must be added to the signature of "
                f"{self.__class__.__qualname__}.configure_user().",
                category=RemovedInDjango50Warning,
            )
            if created:
                user = self.configure_user(request, user)
        return user if self.user_can_authenticate(user) else None

    def clean_username(self, username):
        """Clean the username.

        Perform any cleaning on the "username" prior to using it to get or
        create the user object.  Return the cleaned username.

        By default, return the username unchanged.
        """
        return username

    def configure_user(self, request, user, created=True):
        """Configure a user.

        Configure a user and return the updated user.

        By default, return the user unmodified.
        """
        if created:
            if hasattr(request, "lti_launch"):
                launch: LtiLaunch = request.lti_launch
                user.first_name = launch.user.given_name
                user.last_name = launch.user.family_name
                user.email = launch.user.email
                user.save()
                # associate the Django user with the LTI tool user
                launch.user.auth_user = user
                launch.user.save()
        return user


class AllowAllUsersLtiLaunchAuthenticationBackend(LtiLaunchAuthenticationBackend):
    def user_can_authenticate(self, user):
        return True
