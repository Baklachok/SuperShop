
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_item_brand_item_feature_item_information'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='color',
            name='item',
        ),
        migrations.RemoveField(
            model_name='size',
            name='item',
        ),
    ]
