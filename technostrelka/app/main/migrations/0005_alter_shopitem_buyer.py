# Generated by Django 5.0.4 on 2024-04-15 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_shopitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopitem',
            name='buyer',
            field=models.CharField(default='', max_length=150, null=True),
        ),
    ]
