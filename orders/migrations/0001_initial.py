# Generated by Django 5.0.6 on 2024-07-29 22:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0007_delete_telnocode'),
        ('authentication', '0004_alter_telnocode_expires'),
        ('purchases', '0006_payment_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('created', 'Создан'), ('paid', 'Оплачен'), ('delivered', 'Доставлен'), ('received', 'Получен'), ('canceled', 'Отменен'), ('returned', 'Возвращен')], default='created', max_length=10)),
                ('payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='purchases.payment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.frontenduser')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.itemstock')),
            ],
        ),
    ]
