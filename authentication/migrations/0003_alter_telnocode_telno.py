# Generated by Django 5.0.6 on 2024-07-28 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_telnocode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telnocode',
            name='telNo',
            field=models.CharField(unique=True),
        ),
    ]
