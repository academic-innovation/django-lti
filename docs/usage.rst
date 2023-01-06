Basic Usage
===========

Adding JWKS and OIDC initiation URLs
------------------------------------

To allow LTI platforms to retrieve a JWKS and initiate a launch, add paths for
:class:`lti_tool.views.jwks` and :class:`lti_tool.views.OIDCLoginInitView`
to ``urls.py``

.. code-block:: python

    ...

    from lti_tool.views import jwks, OIDCLoginInitView

    urlpatterns = [
        path(".well-known/jwks.json", jwks, name="jwks"),
        path("init/<uuid:registration_uuid>/", OIDCLoginInitView.as_view(), name="init"),
    ]


Generating and rotating keys
----------------------------

Keys for the JWKS can be generated using the ``rotate_keys`` management command.

.. code-block:: console

    $ python manage.py rotate_keys


Registering an LTI platform
---------------------------

An LTI platform can be registered through the Django admin, or using a custom
interface.

Handling an LTI launch
----------------------

To handle the LTI launch, inherit from :class:`~lti_tool.views.LtiLaunchBaseView` and implement the handler
methods for the types of LTI message types that the application supports.

.. code-block:: python

    class ApplicationLaunchView(LtiLaunchBaseView):

        def handle_resource_launch(self, request, lti_launch):
            ...  # Required. Typically redirects the users to the appropriate page.

        def handle_deep_linking_launch(self, request, lti_launch):
            ...  # Optional.

        def handle_submission_review_launch(self, request, lti_launch):
            ...  # Optional.

        def handle_data_privacy_launch(self, request, lti_launch):
            ...  # Optional.

Each handler method receives the request, as well as a :class:`~lti_tool.models.LtiLaunch` object.

When a session is initiated by an LTI launch, data about the launch is available from
the request at ``request.lti_launch`` as an :class:`~lti_tool.models.LtiLaunch` object. During a non-LTI session
``request.lti_launch`` will refer to an :class:`~lti_tool.models.AbsentLtiLaunch` object.

It is possible to distinguish between :class:`~lti_tool.models.LtiLaunch` and :class:`~lti_tool.models.AbsentLtiLaunch` objects using
the ``.is_present`` and ``.is_absent`` properties.
