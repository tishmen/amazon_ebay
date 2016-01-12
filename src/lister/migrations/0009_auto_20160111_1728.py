# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-11 16:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0008_itemreview_is_listed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemreview',
            name='is_listed',
        ),
        migrations.AddField(
            model_name='amazonitem',
            name='is_listed',
            field=models.BooleanField(default=False),
        ),
    ]