from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from lti_tool.types import LtiLaunch


UserModel = get_user_model()


class LtiLaunchAuthenticationBackend(ModelBackend):
    """
    This backend is to be used in conjunction with the ``LtiLaunchAuthenticationMiddleware``
    found in the middleware module of this package, and is used when authentication is
    is handled by an LMS and passed in via LTI launch.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, request, lti_launch_user_id):
        """
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
        user = self.configure_user(request, user, created=created)
        return user if self.user_can_authenticate(user) else None

    async def aauthenticate(self, request, lti_launch_user_id):
        """See authenticate()."""
        if not lti_launch_user_id:
            return
        created = False
        user = None
        username = self.clean_username(lti_launch_user_id)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = await UserModel._default_manager.aget_or_create(
                **{UserModel.USERNAME_FIELD: username}
            )
        else:
            try:
                user = await UserModel._default_manager.aget_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass
        user = await self.aconfigure_user(request, user, created=created)
        return user if self.user_can_authenticate(user) else None

    def clean_username(self, username):
        """
        Perform any cleaning on the "username" prior to using it to get or
        create the user object.  Return the cleaned username.

        By default, return the username unchanged.
        """
        return username

    def configure_user(self, request, user, created=True):
        """
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
        return user

    async def aconfigure_user(self, request, user, created=True):
        """See configure_user()"""
        return await sync_to_async(self.configure_user)(request, user, created)


class AllowAllUsersLtiLaunchAuthenticationBackend(LtiLaunchAuthenticationBackend):
    def user_can_authenticate(self, user):
        return True
