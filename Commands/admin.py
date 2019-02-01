# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from   .models import runCommands, gromacsSample,serverDetails
from django.contrib import admin

# Register your models here.

admin.site.register(runCommands)
admin.site.register(gromacsSample)
admin.site.register(serverDetails)
