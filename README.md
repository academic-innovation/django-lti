# django-lti

A [Django reusable app](https://docs.djangoproject.com/en/4.0/intro/reusable-apps/) providing support for LTI Advantage.

## Installation

Install using pip.

```
pip install django-lti
```

## Setup

Start by adding `lti_tool` to your project's `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...
    "lti_tool",
]
```

Then, add `lti_tool.middleware.LtiLaunchMiddleware` to the `MIDDLEWARE` setting.
It's important to list the `LtiLaunchMiddleware` _after_ `SessionMiddleware`.

```python
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'lti_tool.middleware.LtiLaunchMiddleware',
]
```

Finally, run migrations to initialize the needed database tables.

```
python manage.py migrate lti_tool
```

## Usage

### Adding JWKS and OIDC initiation URLs

To allow LTI platforms to retrieve a JWKS and initiate a launch, add paths for
`lti_tool.views.jwks` and `lti_tool.views.OIDCLoginInitView` to `urls.py`

```python
...

from lti_tool.views import jwks, OIDCLoginInitView, LtiConfigView

urlpatterns = [
    path(".well-known/jwks.json", jwks, name="jwks"),
    path("init/<uuid:registration_uuid>/", OIDCLoginInitView.as_view(), name="init"),
    path("<uuid:registration_uuid>/config.json", LtiConfigView.as_view()),
]

```

### Generating and rotating keys

Keys for the JWKS can be generated using the `rotate_keys` management command.

```
python manage.py rotate_keys
```

### Registering an LTI platform

An LTI platform can be registered through the Django admin, or using a custom
interface.

### Handling an LTI launch

To handle the LTI launch, inherit from `LtiLaunchBaseView` and implement the handler
methods for the types of LTI message types that the application supports.

```python
class ApplicationLaunchView(LtiLaunchBaseView):

    def handle_resource_launch(self, request, lti_launch):
        ...  # Required. Typically redirects the users to the appropriate page.

    def handle_deep_linking_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_submission_review_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_data_privacy_launch(self, request, lti_launch):
        ...  # Optional.
```

Each handler method receives the request, as well as a `LtiLaunch` object.

When a session is initiated by an LTI launch, data about the launch is available from
the request at `request.lti_launch` as an `LtiLaunch` object. During a non-LTI session
`request.lti_launch` will refer to an `AbsentLtiLaunch` object.

It is possible to distinguish between `LtiLaunch` and `AbsentLtiLaunch` objects using
the `.is_present` and `.is_absent` properties.
