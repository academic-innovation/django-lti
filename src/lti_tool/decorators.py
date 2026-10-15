import functools
import inspect

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _


def lti_launch_required(view_func):
    """Decorator that requires a session associated with a LTI launch."""

    @functools.wraps(view_func)
    async def async_wrapper(request, *args, **kwargs):
        if request.lti_launch.is_absent:
            raise PermissionDenied(
                _("This page may only be accessed through a LTI launch.")
            )
        return await view_func(request, *args, **kwargs)

    @functools.wraps(view_func)
    def sync_wrapper(request, *args, **kwargs):
        if request.lti_launch.is_absent:
            raise PermissionDenied(
                _("This page may only be accessed through a LTI launch.")
            )
        return view_func(request, *args, **kwargs)

    if inspect.iscoroutinefunction(view_func):
        return async_wrapper
    return sync_wrapper
