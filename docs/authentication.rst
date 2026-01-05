Integrating with Django authentication
======================================

Apps can authenticate users using LTI launch data by integrating with Django's authentication system.

Setup
-----

Start by adding ``lti_tool.auth.backends.LtiLaunchAuthenticationBackend`` to your project's ``AUTHENTICATION_BACKENDS``.

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        ...
        'lti_tool.auth.backends.LtiLaunchAuthenticationBackend',
    ]

Then, add ``lti_tool.auth.middleware.LtiLaunchAuthenticationMiddleware`` to the ``MIDDLEWARE`` setting.
It's important to list the ``LtiLaunchAuthenticationMiddleware`` *after* ``LtiLaunchMiddleware`` and
``AuthenticationMiddleware``.

.. code-block:: python

    MIDDLEWARE = [
        'lti_tool.middleware.LtiLaunchMiddleware',
        ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'lti_tool.auth.middleware.LtiLaunchAuthenticationMiddleware',
    ]

Configuring the Django username
-------------------------------

By default, the username is set to the ``sub`` value from the LTI launch.  You can use the ``person_sourcedid``
value from the ``lis`` claim instead by adding this to your Django settings:

.. code-block:: python

    LTI_TOOL = {
        'use_person_sourcedid': True,
    }

If you want to use a different field, you can subclass ``LtiLaunchAuthenticationBackend`` and override the
``get_username`` method.