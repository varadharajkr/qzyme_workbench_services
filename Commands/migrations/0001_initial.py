# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-27 07:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='runCommands',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('PreCommand', models.CharField(max_length=10)),
                ('FileInput', models.CharField(max_length=5)),
                ('Size', models.FloatField()),
                ('NumRun', models.IntegerField()),
            ],
        ),
    ]
