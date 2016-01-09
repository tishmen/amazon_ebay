# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-08 16:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lister', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=80)),
                ('category', models.IntegerField()),
                ('html', models.TextField()),
                ('upc', models.CharField(blank=True, max_length=12, null=True)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lister.AmazonItem')),
            ],
        ),
    ]