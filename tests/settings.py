DEBUG = True
USE_TZ = True
USE_I18N = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
ROOT_URLCONF = "tests.urls"
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "lti_tool.middleware.LtiLaunchMiddleware",
    "lti_tool.middleware.LtiEmbedMiddleware",
]
SECURE_CSP = {"default-src": ["'self'"], "frame-ancestors": ["'self'"]}
SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "lti_tool",
]
SECRET_KEY = "test-secret-key"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
