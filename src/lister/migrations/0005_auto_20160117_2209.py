# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-17 21:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0004_ebayitem_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amazonitem',
            name='review_count',
            field=models.PositiveIntegerField(verbose_name='reviews'),
        ),
    ]