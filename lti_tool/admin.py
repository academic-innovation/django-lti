from django.contrib import admin

from . import models


class LtiDeploymentInline(admin.TabularInline):
    model = models.LtiDeployment


@admin.register(models.LtiRegistration)
class LtiRegistrationAdmin(admin.ModelAdmin):
    inlines = [LtiDeploymentInline]
