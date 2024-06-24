OIDC Initiation
===============

LTI launches use the `OIDC third-party initiation flow`_ as a security measure to prevent
CSRF attacks. As a part of this workflow, an LTI tool must:

1. Receive an `initiation request`_ from a registered platform.
2. Respond with a properly formed `authentication request`_.

Handling an initiation request
------------------------------

To handle an initiation request from an LTI platform, ``django-lti`` provides
:class:`~lti_tool.views.OIDCLoginInitView`, which can be used as-is in a Django project
to return an authentication request to the platform

.. code-block:: python

    ...

    from lti_tool.views import OIDCLoginInitView

    urlpatterns = [
        path("init/<uuid:registration_uuid/", OIDCLoginInitView.as_view(
            main_msg=(
                "Your browser prevents embedded content from using cookies.  To work "
                "around this, the content must be opened in a new tab or window.  "
            ),
            click_msg="Open a new tab or window now.",
            loading_msg="Loading..."
        ), name="init"),
        # ...
    ]

The ``registration_uuid`` parameter is a reference to the
:attr:`LtiRegistration.uuid <lti_tool.models.LtiRegistration.uuid>` property, and is
used to identify the platform registration associated with the initiation request.

The ``main_msg``, ``click_msg``, and ``loading_msg`` **optional** arguments are
passed to ``DjangoOIDCLogin.enable_check_cookies()`` to generate messages shown
in the UI.  The values shown here are the default values used by
``OIDCLoginInitView``.  If cookies are not allowed by the browser, the value of
``main_msg`` will be shown.  That will be followed by a link with label
containing the value of ``click_msg``, which opens the content in a new tab or
window.

Customizing the authentication request
--------------------------------------

By default, the response from :class:`~lti_tool.views.OIDCLoginInitView` will use the
``target_link_uri`` from the request as the ``redirect_uri``. If the application
requires the use of a different ``redirect_uri`` it can be provided by overriding the
:meth:`~lti_tool.views.OIDCLoginInitView.get_redirect_url` method.

.. code-block:: python

    class CustomLoginInitView(OIDCLoginInitView):
        def get_redirect_url(self, target_link_uri):
            return "https://my.tool/some/custom/path/"

Resources
---------

- `OpenID Connect Launch Flow Overview`_ described in the 1EdTech Security Framework.
- `Additional login parameters`_ described by the LTI 1.3 Core Specification.
- `LTI 1.3 Security and OpenID Connect`_ explains the CSRF vulnerability that is
  addressed by the third-party initiation flow.


.. _initiation request: https://www.imsglobal.org/spec/security/v1p0/#step-1-third-party-initiated-login
.. _authentication request: https://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request
.. _OIDC third-party initiation flow: https://www.imsglobal.org/spec/security/v1p0/#openid_connect_launch_flow

.. _OpenID Connect Launch Flow Overview: https://www.imsglobal.org/spec/security/v1p0/#step-1-third-party-initiated-login
.. _Additional login parameters: https://www.imsglobal.org/spec/lti/v1p3/#additional-login-parameters
.. _LTI 1.3 Security and OpenID Connect: https://youtu.be/d_Otmti7xKA
