# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-15 13:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0003_ebayitem_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='ebayitem',
            name='error',
            field=models.TextField(blank=True, null=True),
        ),
    ]
