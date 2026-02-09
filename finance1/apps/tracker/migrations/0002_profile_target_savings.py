# Generated migration: add target_savings to Profile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='target_savings',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12),
        ),
    ]
