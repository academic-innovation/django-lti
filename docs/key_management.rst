Key management
==============

LTI messages are signed by key-pairs (private and public key), and ``django-lti``
provides helpers for generating and managing keys.

The ``Key`` model
-----------------

In ``django-lti``, keys are stored in the database using the
:class:`~lti_tool.models.Key` model. During typical usage, there is no need for an
application to use the ``Key`` model directly. Instead, keys can be generated and
deactivated using a management command.

Rotating keys
-------------

Keys can be rotated using the ``rotate_keys`` management command. The
``--deactivate_after`` option may be specified to indicate the
amount of days after which keys should be deactivated.

If desired, a cronjob can be configured to rotate and deactivate keys
on a regular schedule.

.. code-block:: text

    0 0 * * 0 /path/to/python /path/to/manage.py rotate_keys

Exposing a key set URL
----------------------

Tools must make their public keys available to platforms through a `key set URL`_.
The :func:`~lti_tool.views.jwks` view is provided by ``django-lti`` for this purpose.

.. code-block:: python

    from lti_tool.views import jwks

    urlpatterns = [
        path(".well-known/jwks.json", jwks, name="jwks"),
        ...
    ]

Resources
---------

Details of how key-pairs are used by LTI tools are described in the
`1EdTech Security Framework`_.

* `Securing Web Services`_
* `Message Security and Message Signing`_
* `Key Management`_


.. _key set URL: https://www.imsglobal.org/spec/security/v1p0/#h_key-set-url
.. _1EdTech Security Framework: https://www.imsglobal.org/spec/security/v1p0/
.. _Securing Web Services: https://www.imsglobal.org/spec/security/v1p0/#securing_web_services
.. _Message Security and Message Signing: https://www.imsglobal.org/spec/security/v1p0/#message-security-and-message-signing
.. _Key Management: https://www.imsglobal.org/spec/security/v1p0/#h_key-management
