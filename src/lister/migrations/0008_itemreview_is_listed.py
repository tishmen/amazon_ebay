# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-10 21:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0007_auto_20160110_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemreview',
            name='is_listed',
            field=models.BooleanField(default=False),
        ),
    ]
