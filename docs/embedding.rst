Supporting Embedding
====================

To allow embedding LTI launches in learning platforms, ``django-lti`` provides
middleware that interacts with Django's built-in CSP support.

.. warning::
   This feature requires Django 6.0+, which added built-in support for Content Security
   Policy.

Enabling support
----------------

To enable support add :class:`~lti_tool.middleware.LtiEmbedMiddleware` to the
``MIDDLEWARE`` setting.

.. code-block:: python

    MIDDLEWARE = [
        ...
        "django.middleware.csp.ContentSecurityPolicyMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "lti_tool.middleware.LtiLaunchMiddleware",
        "lti_tool.middleware.LtiEmbedMiddleware",
    ]

Be sure that :class:`~lti_tool.middleware.LtiEmbedMiddleware` is listed *after*
``ContentSecurityPolicyMiddleware`` and
:class:`~lti_tool.middleware.LtiLaunchMiddleware`.

Specifying embed domains
------------------------

Domains where a tool can be embedded are distinct for each registered platform. Domains
for each :class:`~lti_tool.models.LtiRegistration` may be specified, as
:class:`~lti_tool.models.EmbedDomain` objects, when creating or editing the registration
in the Django admin.

Domains are added to the ``frame-ancestors`` directive of responses for:

- An LTI launch, and later requests in a session started by that launch.
- The OIDC initiation view, :class:`~lti_tool.views.OIDCLoginInitView`, once the
  registration has been identified. When a platform embeds the tool, this is the first
  page it loads in the frame.

Responses to other requests, and responses for registrations with no domains, are not
modified.

The domains are merged into any ``frame-ancestors`` value in Django's ``SECURE_CSP``
setting. If ``SECURE_CSP`` has no ``frame-ancestors`` directive, one is added that
contains only the embed domains.

If ``SECURE_CSP_REPORT_ONLY`` has a ``frame-ancestors`` directive, the domains are
merged into it too, so platforms embedding the tool don't produce violation reports.
A report-only policy without ``frame-ancestors`` is left as is.

Views that override a policy are not modified by
:class:`~lti_tool.middleware.LtiEmbedMiddleware`. ``@csp_override`` leaves the
``SECURE_CSP`` policy alone, and ``@csp_report_only_override`` leaves the
``SECURE_CSP_REPORT_ONLY`` policy alone. The two are handled independently, so a
view that overrides only one policy still has the domains merged into the other.

Caching settings
----------------

By default, :class:`~lti_tool.middleware.LtiEmbedMiddleware` will try to cache embed
domain lookups for each registration in the default cache with an expiration of 5
minutes. A different cache alias and timeout value may be specified by the
``LTI_TOOL_EMBED_CACHE`` and ``LTI_TOOL_EMBED_CACHE_TIMEOUT`` settings respectively. A
timeout of ``0`` disables caching.

.. note::
   Django's default cache is local to each process. With several worker processes, a
   change may not reach every worker until the timeout expires. Use a shared cache
   backend, or a shorter timeout, if domain changes need to take effect quickly.

Resources
---------

- `frame-ancestors`_ from MDN
- `Django's CSP docs`_


.. _frame-ancestors: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors
.. _Django's CSP docs: https://docs.djangoproject.com/en/6.0/ref/csp/
