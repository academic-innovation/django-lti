Handling a Launch
=================

The ``django-lti`` library aims to make the handling of LTI launch messages as
straightforward as possible, while still allowing the flexibility to implement required
application-specific functionality.

Implementing a Launch view
--------------------------

To aid tool development ``django-lti`` provides
:class:`~lti_tool.views.LtiLaunchBaseView`, a base view which handles many of the tasks
that a typical Django-based LTI tool will need to address on every launch.

- Clearing any preexisting session data
- Validating the launch data
- Synchronizing any launch data from the platform with the tools internal data
  model
- Adding a launch ID to the session so that launch data can be retrieved during future
  requests

This still leaves any application-specific details, which can be implemented by
overriding the :meth:`~lti_tool.views.LtiLaunchBaseView.handle_resource_launch`
method.

.. code-block:: python

    class ApplicationLaunchView(LtiLaunchBaseView):

        def handle_resource_launch(self, request, lti_launch):
            ...  # Application-specific launch handling can happen here.

Each application will handle a launch differently, but common tasks include:

- Associating the launch user with an application user account
- Starting an asynchronous task to fetch course members from the platform
- Redirecting to an appropriate page based on launch data

Other Launch Messages
---------------------

While the majority of LTI launches will be ``LtiResourceLinkRequest`` messages handled
through ``handle_resource_launch``, ``LtiLaunchBaseView`` provides other methods for
handling launches with different messages.

.. csv-table:: Message types and handlers
   :header: LTI message type, ``LtiLaunchBaseView`` method

   ``LtiResourceLinkRequest``, :meth:`~lti_tool.views.LtiLaunchBaseView.handle_resource_launch`
   ``LtiDeepLinkingRequest``, :meth:`~lti_tool.views.LtiLaunchBaseView.handle_deep_linking_launch`
   ``LtiSubmissionReviewRequest``, :meth:`~lti_tool.views.LtiLaunchBaseView.handle_submission_review_launch`
   ``DataPrivacyLaunchRequest``, :meth:`~lti_tool.views.LtiLaunchBaseView.handle_data_privacy_launch`

By default, all messages other than ``LtiResourceLinkRequest`` return a message
indicating that the message type is not supported.

Resources
---------

- `LTI launch`_ definition from the LTI 1.3 Core Specification.
- `Resource link launch request message`_ description from the LTI 1.3 Core
  Specification.


.. _LTI launch: https://www.imsglobal.org/spec/lti/v1p3/#lti-launch
.. _Resource link launch request message: https://www.imsglobal.org/spec/lti/v1p3/#resource-link-launch-request-message
