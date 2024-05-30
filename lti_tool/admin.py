from django.contrib import admin
from django.utils.translation import gettext as _

from . import models


class LtiDeploymentInline(admin.TabularInline):
    model = models.LtiDeployment


@admin.register(models.LtiRegistration)
class LtiRegistrationAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "uuid",
                    "issuer",
                    "client_id",
                    "auth_url",
                    "token_url",
                    "keyset_url",
                    "is_active",
                ]
            },
        ),
        (
            _("Static keys"),
            {
                "description": _("For platforms not supporting JWK Set use by tools."),
                "fields": ["public_key", "private_key"],
                "classes": ["collapse"],
            },
        ),
    ]
    inlines = [LtiDeploymentInline]
