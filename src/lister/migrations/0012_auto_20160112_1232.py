# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-12 11:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0011_itemreview_category_search'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amazonsearch',
            name='query',
            field=models.TextField(),
        ),
    ]
