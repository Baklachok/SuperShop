# Generated by Django 5.0.6 on 2024-07-29 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0002_review_reviewphoto'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='text',
        ),
        migrations.AddField(
            model_name='review',
            name='advantages',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='disadvantages',
            field=models.TextField(blank=True, null=True),
        ),
    ]
