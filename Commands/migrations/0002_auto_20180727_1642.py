# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-27 11:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Commands', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='gromacsSample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abc', models.CharField(max_length=25)),
                ('fgh', models.IntegerField()),
            ],
        ),
        migrations.AlterField(
            model_name='runcommands',
            name='PreCommand',
            field=models.CharField(max_length=20),
        ),
    ]
