# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class runCommands(models.Model):
    PreCommand = models.CharField(max_length=20)
    FileInput = models.CharField(max_length=5)
    Size = models.FloatField()
    NumRun = models.IntegerField()

    def __str__(self):
        return self.PreCommand

class gromacsSample(models.Model):
    abc = models.CharField(max_length=25)
    fgh = models.IntegerField()

    def __str__(self):
        return self.abc

class serverDetails(models.Model):
    idqzw_server_service_details = models.IntegerField(primary_key=True)
    server_id = models.CharField(max_length=11)
    service_url = models.CharField(max_length=150)
    command_tool_id = models.CharField(max_length=150)

    class Meta:
        db_table = "qzw_server_service_details"

    def __str__(self):
        return u'%s %s %s %s' % (self.idqzw_server_service_details,self.server_id,self.service_url,self.command_tool_id)

class commandDetails(models.Model):
    command_id = models.IntegerField(primary_key=True)
    project_id = models.IntegerField()
    user_id = models.IntegerField()
    primary_command = models.TextField()
    entry_time = models.DateTimeField()
    status = models.IntegerField()
    command_tool = models.CharField(max_length=150)
    command_title = models.CharField(max_length=200)
    comments = models.TextField()

    class Meta:
        db_table = "qzw_project_commands"

    def __str__(self):
        return u'%s %s %s %s %s %s %s %s %s' % (self.command_id,self.project_id,self.user_id,self.primary_command,self.entry_time,self.status,self.command_tool,self.command_title,self.comments)

class QzwProjectDetails(models.Model):
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=100)
    project_status = models.CharField(max_length=50)
    project_description = models.TextField()
    project_category = models.IntegerField()
    project_investigator = models.IntegerField()
    project_code = models.CharField(max_length=100)
    enabled = models.IntegerField()
    project_json = models.TextField(blank=True, null=True)
    json_selected_text = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'qzw_project_details'

    def __str__(self):
        return u'%s %s %s %s %s %s %s %s' % (self.project_id,self.project_name,self.project_status,self.project_description,self.project_category,self.project_investigator,self.project_code,self.enabled)

class ProjectToolEssentials(models.Model):
    tool_title = models.TextField(blank=True, null=True)
    project_id = models.IntegerField(blank=True, null=True)
    key_name = models.TextField(blank=True, null=True)
    values = models.TextField(blank=True, null=True)
    entry_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'project_tool_essentials'

    def __str__(self):
        return u'%s %s %s %s %s' % (self.tool_title,self.project_id,self.key_name,self.values,self.entry_time)


class QzwSlurmJobDetails(models.Model):
    user_id = models.IntegerField()
    project_id = models.IntegerField()
    entry_time = models.DateTimeField()
    job_id = models.IntegerField()
    job_status = models.CharField(max_length=45, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'qzw_slurm_job_details'

    def __str__(self):
        return u'%s %s %s %s %s %s' % (self.user_id,self.project_id,self.entry_time,self.job_id,self.job_status,self.job_title)

class QzwProjectEssentials(models.Model):
    id = models.AutoField(primary_key=True)
    project_id = models.IntegerField()
    command_title = models.CharField(max_length=150, blank=True, null=True)
    command_id = models.IntegerField(blank=True, null=True)
    command_tool = models.CharField(max_length=150, blank=True, null=True)
    command_key = models.CharField(max_length=100, blank=True, null=True)
    command_value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'qzw_project_essentials'

    def __str__(self):
        return u'%s %s %s %s %s %s' % (self.project_id,self.command_title,self.command_id,self.command_tool,self.command_key,self.command_value)

class QzwResearchPapers(models.Model):
    idqzw_research_papers = models.AutoField(primary_key=True)
    research_paper_title = models.TextField(blank=True, null=True)
    research_paper_url = models.TextField(blank=True, null=True)
    research_paper_citations = models.IntegerField(blank=True, null=True)
    research_paper_version = models.CharField(max_length=45, blank=True, null=True)
    research_paper_doi = models.TextField(blank=True, null=True)
    research_paper_pdf_link = models.TextField(blank=True, null=True)
    research_paper_keywords = models.TextField(blank=True, null=True)
    research_paper_abstract = models.TextField(blank=True, null=True)
    publication_year = models.CharField(max_length=45, blank=True, null=True)
    author_name = models.TextField(blank=True, null=True)
    journal_name = models.TextField(blank=True, null=True)
    search_source = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'qzw_research_papers'

        # defining a method to return all fields
    def __str__(self):
        return u'%s %s %s %s %s %s %s %s %s %s %s %s' % (
            self.research_paper_title,
            self.research_paper_url,
            self.research_paper_citations,
            self.research_paper_version,
            self.research_paper_doi,
            self.research_paper_pdf_link,
            self.research_paper_keywords,
            self.research_paper_abstract,
            self.publication_year,
            self.author_name,
            self.journal_name,
            self.search_source)
