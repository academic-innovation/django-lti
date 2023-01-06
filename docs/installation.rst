Installation and Setup
======================

Requirements
------------

* Python >= 3.6
* Django >= 3.2

Installation
------------

Install using ``pip``.

.. code-block:: console

    $ pip install django-lti

Setup
-----

Start by adding ``lti_tool`` to your project's ``INSTALLED_APPS``.

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "lti_tool",
    ]

Then, add ``lti_tool.middleware.LtiLaunchMiddleware`` to the ``MIDDLEWARE`` setting.
It's important to list the ``LtiLaunchMiddleware`` *after* ``SessionMiddleware``.

.. code-block:: python

    MIDDLEWARE = [
        ...
        'django.contrib.sessions.middleware.SessionMiddleware',
        'lti_tool.middleware.LtiLaunchMiddleware',
    ]

Finally, run migrations to initialize the needed database tables.

.. code-block:: console

    $ python manage.py migrate lti_tool
