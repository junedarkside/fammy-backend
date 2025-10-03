# Generated manually to remove unused ProviderMeta model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0005_provider_is_active'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProviderMeta',
        ),
    ]
