# Generated migration for CheckIn Group provider

from django.db import migrations


def create_checkingroup_provider(apps, schema_editor):
    """
    Create CheckIn Group provider record.

    CheckIn Group is a Thai B2B travel wholesaler with public API.
    - Base URL: https://api.checkingroup.co.th
    - Authentication: None (public API)
    - Data Quality: 85/100
    """
    Provider = apps.get_model('wholesale', 'Provider')
    Provider.objects.create(
        code='checkingroup',
        name='CheckIn Group',
        base_url='https://api.checkingroup.co.th',
        token='',
        is_active=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0007_programtour_data_quality_score_and_more'),
    ]

    operations = [
        migrations.RunPython(create_checkingroup_provider),
    ]
