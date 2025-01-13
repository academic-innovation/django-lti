from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lti_tool", "0005_ltilineitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="ltiregistration",
            name="audience",
            field=models.CharField(blank=True, max_length=255, verbose_name="audience"),
        ),
    ]
