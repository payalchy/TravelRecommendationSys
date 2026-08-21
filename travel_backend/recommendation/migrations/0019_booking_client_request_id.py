from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommendation', '0018_merge_20260722_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='client_request_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
