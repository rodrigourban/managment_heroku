# Generated by Django 3.0.5 on 2020-04-12 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_auto_20200405_0244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='image',
            field=models.ImageField(default='default.png', upload_to='images'),
        ),
    ]
