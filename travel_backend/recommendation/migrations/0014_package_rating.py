from django.db import migrations, models
from django.core.validators import MaxValueValidator, MinValueValidator
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recommendation', '0013_booking_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='travelpackage',
            name='average_rating',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='travelpackage',
            name='rating_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='PackageRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='recommendation.travelpackage')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='package_ratings', to='auth.user')),
            ],
            options={
                'unique_together': {('package', 'user')},
                'indexes': [models.Index(fields=['package', 'user'], name='recommendation_packag_package_28a0c2_idx')],
            },
        ),
    ]
