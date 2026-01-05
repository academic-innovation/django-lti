:tocdepth: 3

API Reference
=============

LTI Views
---------

.. autofunction:: lti_tool.views.jwks

.. autoclass:: lti_tool.views.OIDCLoginInitView
   :members:

.. autoclass:: lti_tool.views.LtiLaunchBaseView
   :members:
   :undoc-members:
   :exclude-members: post, dispatch
   :member-order: bysource

LTI launch data
---------------

When using ``django-lti``, LTI launch data is accessed through the ``LtiLaunch`` class.

.. autoclass:: lti_tool.models.LtiLaunch
   :members:
   :undoc-members:
   :exclude-members:
      get_launch_id,
      get_message_launch,
      get_launch_data,
      get_claim,
      ags_claim,
      context_claim,
      roles_claim,
      resource_link_claim,
      platform_instance_claim,
      nrps_claim,
      launch_presentation_claim

For requests in a non-LTI conext, an ``AbsentLtiLaunch`` will be present.

.. autoclass:: lti_tool.models.AbsentLtiLaunch
   :members:
   :undoc-members:

LTI Models
----------

Django database models are provided by ``django-lti`` to represent the configuration
and components of an LTI launch.

.. autoclass:: lti_tool.models.LtiRegistration
   :members:
   :exclude-members: DoesNotExist, MultipleObjectsReturned


LTI Authentication
------------------

``django-lti`` provides a custom authentication backend and middleware to authenticate
users using LTI launch data.

.. autoclass:: lti_tool.auth.backends.LtiLaunchAuthenticationBackend
   :members:

.. autoclass:: lti_tool.auth.middleware.LtiLaunchAuthenticationMiddleware
   :members: