# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-12 12:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0012_auto_20160112_1232'),
    ]

    operations = [
        migrations.CreateModel(
            name='EbayItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField()),
                ('url', models.URLField(unique=True)),
                ('review', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lister.ItemReview')),
            ],
        ),
    ]