# Generated by Django 3.2.9 on 2022-02-08 16:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lti_tool', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LtiContext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_on_platform', models.CharField(blank=True, max_length=255, verbose_name='ID on platform')),
                ('label', models.CharField(blank=True, max_length=255, verbose_name='label')),
                ('title', models.CharField(blank=True, max_length=500, verbose_name='title')),
                ('is_course_template', models.BooleanField(default=False, verbose_name='is course template')),
                ('is_course_offering', models.BooleanField(default=False, verbose_name='is course offering')),
                ('is_course_section', models.BooleanField(default=False, verbose_name='is course section')),
                ('is_group', models.BooleanField(default=False, verbose_name='is group')),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('datetime_modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'verbose_name': 'LTI context',
                'verbose_name_plural': 'LTI contexts',
            },
        ),
        migrations.CreateModel(
            name='LtiMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_administrator', models.BooleanField(default=False, verbose_name='is administrator')),
                ('is_content_developer', models.BooleanField(default=False, verbose_name='is_content_developer')),
                ('is_instructor', models.BooleanField(default=False, verbose_name='is instructor')),
                ('is_learner', models.BooleanField(default=False, verbose_name='is learner')),
                ('is_mentor', models.BooleanField(default=False, verbose_name='is mentor')),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('datetime_modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'verbose_name': 'LTI membership',
                'verbose_name_plural': 'LTI memberships',
            },
        ),
        migrations.CreateModel(
            name='LtiPlatformInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issuer', models.CharField(max_length=255, verbose_name='issuer')),
                ('guid', models.CharField(max_length=255, verbose_name='GUID')),
                ('contact_email', models.EmailField(blank=True, max_length=254, verbose_name='contact email')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('name', models.CharField(blank=True, max_length=500, verbose_name='name')),
                ('url', models.URLField(blank=True, verbose_name='URL')),
                ('product_family_code', models.CharField(blank=True, max_length=500, verbose_name='product family code')),
                ('version', models.CharField(blank=True, max_length=500, verbose_name='version')),
            ],
            options={
                'verbose_name': 'LTI platform instance',
                'verbose_name_plural': 'LTI platform instances',
            },
        ),
        migrations.CreateModel(
            name='LtiUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub', models.CharField(max_length=255, verbose_name='subject')),
                ('given_name', models.CharField(blank=True, max_length=500, verbose_name='given name')),
                ('family_name', models.CharField(blank=True, max_length=500, verbose_name='family name')),
                ('name', models.CharField(blank=True, max_length=500, verbose_name='name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email')),
                ('picture_url', models.URLField(blank=True, verbose_name='picture URL')),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('datetime_modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('auth_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lti_users', to=settings.AUTH_USER_MODEL, verbose_name='auth user')),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='lti_tool.ltiregistration', verbose_name='registration')),
            ],
            options={
                'verbose_name': 'LTI user',
                'verbose_name_plural': 'LTI users',
            },
        ),
        migrations.CreateModel(
            name='LtiResourceLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_on_platform', models.CharField(max_length=255, verbose_name='ID on platform')),
                ('title', models.CharField(blank=True, max_length=500, verbose_name='title')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('datetime_modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('context', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resource_links', to='lti_tool.lticontext', verbose_name='context')),
            ],
            options={
                'verbose_name': 'LTI resource link',
                'verbose_name_plural': 'LTI resource links',
            },
        ),
        migrations.AddConstraint(
            model_name='ltiplatforminstance',
            constraint=models.UniqueConstraint(fields=('issuer', 'guid'), name='unique_guid_per_issuer'),
        ),
        migrations.AddField(
            model_name='ltimembership',
            name='context',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='lti_tool.lticontext', verbose_name='context'),
        ),
        migrations.AddField(
            model_name='ltimembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='lti_tool.ltiuser', verbose_name='user'),
        ),
        migrations.AddField(
            model_name='lticontext',
            name='deployment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contexts', to='lti_tool.ltideployment', verbose_name='deployment'),
        ),
        migrations.AddField(
            model_name='lticontext',
            name='members',
            field=models.ManyToManyField(related_name='contexts', through='lti_tool.LtiMembership', to='lti_tool.LtiUser', verbose_name='members'),
        ),
        migrations.AddField(
            model_name='ltideployment',
            name='platform_instance',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deployments', to='lti_tool.ltiplatforminstance', verbose_name='platform instance'),
        ),
        migrations.AddConstraint(
            model_name='ltiuser',
            constraint=models.UniqueConstraint(fields=('registration', 'sub'), name='unique_sub_per_registration'),
        ),
        migrations.AddConstraint(
            model_name='ltiresourcelink',
            constraint=models.UniqueConstraint(fields=('context', 'id_on_platform'), name='unique_resource_link_id_per_context'),
        ),
        migrations.AddConstraint(
            model_name='ltimembership',
            constraint=models.UniqueConstraint(fields=('user', 'context'), name='no_duplicate_memberships'),
        ),
        migrations.AddConstraint(
            model_name='lticontext',
            constraint=models.UniqueConstraint(fields=('deployment', 'id_on_platform'), name='unique_context_id_per_deployment'),
        ),
    ]
