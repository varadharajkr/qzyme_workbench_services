# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import sys
import commands

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import request
from rest_framework import status
from .models import runCommands, gromacsSample, serverDetails, commandDetails, QzwProjectDetails, QzwResearchPapers, \
    ProjectToolEssentials, QzwSlurmJobDetails, QzEmployeeEmail
from .serializers import runCommandSerializer , serverrDetailsSerializer
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django import db
from django.db import connections
import subprocess
from subprocess import PIPE, Popen, call
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import shutil
import re
import config
import os
from os import listdir
import errno
import ast
import time
from datetime import datetime
import glob
import urllib2
from urllib import urlopen
import json
import requests
import MySQLdb
from multiprocessing import Process
from urlparse import urljoin
from bs4 import BeautifulSoup
from django import db
import logging # for default django logging
# Create your views ere.

django_logger = logging.getLogger(__name__)


# to run command in shell
def execute_command(command,inp_command_id,user_email_string,project_name,project_id, command_tool,command_title,job_id=''):
    print('inside execute_command')
    print('command to execute is ',command)
    print('inp command id is ',inp_command_id)
    status_id = config.CONSTS['status_initiated']
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    print("execute command in execute command function")
    # process.wait()
    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
    return process


# to run command in shell
def execute_umbrella_sampling_command(command,inp_command_id,user_email_string,project_name,project_id, command_tool,command_title,job_id=''):
    print('inside execute_umbrella_sampling_command')
    print('command to execute is ',command)
    print('inp command id is ',inp_command_id)
    print("job_id is ",job_id)
    status_id = config.CONSTS['status_initiated']
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    print("execute command in execute command function")
    # process.wait()
    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
    return process


def execute_fjs_command(command,inp_command_id,program_path,command_title,user_email_string,project_name, project_id, command_tool):
    print('FJS command to execute is ',command)
    print('FJS inp command id is ',inp_command_id)
    status_id = config.CONSTS['status_initiated']
    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title)
    logfile = open(str(program_path)+str(command_title)+'.log', 'w+')
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    for line in process.stdout:
        sys.stdout.write(line)
        if "Submitted batch job" in line:
            # filtering jobID from string
            slurm_jobid = int(''.join(list(filter(str.isdigit, line))))
            # query to Slurm sacct
            slurm_sacct_query = subprocess.check_output(
                "sacct --format='JobID,JobName%30,Partition,AllocCPUS,State,ExitCode' -j "+str(slurm_jobid)+"", shell=True);
            
            with open(program_path+'temp_sacct_details.txt', 'w+') as out:
                out.write(slurm_sacct_query.decode())
            with open(program_path+'temp_sacct_details.txt', 'r') as file:
                for line in file:
                    if line.startswith(str(slurm_jobid)+" "):
                        JobID, JobName, Partition, AllocCPUS, State, ExitCode = line.split()[0], line.split()[1], \
                                                                                line.split()[2], line.split()[3], \
                                                                                line.split()[4], line.split()[5]
                        try:
                            db.close_old_connections()
                            # get command details
                            entry_time = datetime.now()
                            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
                            project_id = commandDetails_result.project_id
                            user_id = commandDetails_result.user_id
                            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                project_id=project_id,
                                                                                entry_time=entry_time,
                                                                                job_id=JobID,
                                                                                job_status=State,
                                                                                job_title=JobName,
                                                                                job_details=JobName,
                                                                                command_id=inp_command_id)
                            QzwSlurmJobDetails_save_job_id.save()
                            # update details to DB
                        except db.OperationalError as e:
                            db.close_old_connections()
            os.remove(program_path+'temp_sacct_details.txt')

        logfile.write(line)
    print("execute command in execute command function")
    # process.wait()
    return process


def execute_command_md_run(command, change_dir,source_file_path):
    print("in md popen-----")
    print(change_dir)
    os.chdir(source_file_path)
    print("after go back")
    print(os.getcwd())
    os.chdir(change_dir)
    print("change to working again")
    print(os.getcwd())
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    print("execute command md run")
    process.wait()
    return process

# commands/
class gromacsCommands(APIView):

    def get(self, request):
        commands = runCommands.objects.all()
        serializer = runCommandSerializer(commands, many=True)
        return Response(serializer.data)

    def post(self):
        pass


class getserverDetails(APIView):

    def get(self,request):
        # c = connections['default'].cursor()
        # c.execute("SELECT * FROM qzw_server_service_details")
        # rows = c.fetchall()
        # print rows

        qzw_server_service_details = serverDetails.objects.all()
        serializer = serverrDetailsSerializer(qzw_server_service_details,many=True)
        return Response(serializer.data)

    def post(self):
        pass

def grom(request):
    inp_command_id = 7 #request.POST.get("command_id")
    commandDetails_result = commandDetails.objects.all().filter(command_id=inp_command_id)
    print(commandDetails_result)


class gromacs(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id)) #get group project
        print('before replacing primary_command_runnable')
        print(primary_command_runnable)


        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+group_project_name+'/'+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ group_project_name+'/'+project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+ project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + commandDetails_result.command_tool +'/')
        print(os.system("pwd"))
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)
        if process_return.returncode == 0:
            print("inside success")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+'/'+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("inside error")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


@csrf_exempt
def generate_modeller_catmec_slurm_script(file_path, server_name, job_name, pre_slurm_script_file_name, slurm_script_file_name,primary_command_runnable):
    print('inside generate_modeller_slurm_script function')
    print("primary_command_runnable is ",primary_command_runnable)
    print(file_path + '/' + pre_slurm_script_file_name)
    print(file_path +'/'+ slurm_script_file_name)
    new_shell_script_lines = ''
    print("str(config.CONSTS['modeller_catmec_number_of_threads'])")
    print(str(config.CONSTS['modeller_catmec_number_of_threads']))
    number_of_threads = str(config.CONSTS['modeller_catmec_number_of_threads'])
    print('before opening ',file_path +'/'+ pre_slurm_script_file_name)
    with open(file_path +'/'+ pre_slurm_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ pre_slurm_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ slurm_script_file_name):
        print('removing ',file_path + slurm_script_file_name)
        os.remove(file_path + '/' + slurm_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ slurm_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ slurm_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write(str(primary_command_runnable)+"\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True


@csrf_exempt
def generate_TASS_slurm_script(file_path, server_name, job_name, pre_simulation_script_file_name, simulation_script_file_name,number_of_threads, command_title, plumed_command=''):
    print('inside generate_TASS_slurm_script function')
    print('file_path ',)
    print('server_name ',server_name)
    print('job_name ',job_name)
    print('number_of_threads ',number_of_threads)
    new_shell_script_lines = ''
    print('before opening ',file_path +'/'+ pre_simulation_script_file_name)
    with open(file_path +'/'+ pre_simulation_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ pre_simulation_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            elif 'PLUMED_COMMAND_REPLACEMENT' in line:
                new_shell_script_lines += (line.replace('PLUMED_COMMAND_REPLACEMENT',str(plumed_command)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ simulation_script_file_name):
        print('removing ',file_path + simulation_script_file_name)
        os.remove(file_path + '/' + simulation_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ simulation_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ simulation_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        if command_title == 'nvt_equilibration':
            new_bash_script.write("sander -O -i Heat.in -o Heat.out -p amber.top -c 01_Min.ncrst -r Heat.ncrst -x Heat.nc -inf Heat.mdinfo\n")
        elif command_title == 'nvt_simulation':
            new_bash_script.write("sander -O -i test.in -o min_qmmm.out -p amber.top -c Heat.ncrst -r min_qmmm.rst\n")
        elif command_title == 'TASS_qmm_mm':
            new_bash_script.write("sander -O -i md_qmm.in -o md_qmmm.out -p amber.top -c Heat.ncrst -r md_qmmm.rst -x md_qmmm.mdcrd\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True


@csrf_exempt
def replace_temp_and_nsteps_in_inp_file(file_path, pre_inp_file,  inp_file, temp_value='', nsteps_value='', atom_range='', net_charge_value=''):
    print('inside replace_temp_and_nsteps_in_inp_file function')
    print(file_path+pre_inp_file)
    print(file_path+inp_file)
    print('temp_value ',temp_value)
    print('nsteps_value ',nsteps_value)
    print('atom_range ',atom_range)
    print('net_charge_value ',net_charge_value)
    try:
        original_inp_lines = ''
        with open(file_path+pre_inp_file, 'r') as pre_processed_mdb:
            content = pre_processed_mdb.readlines()
            for line in content:
                if 'QZTEMP' in line or 'QZNSTEPS' in line or 'QZATMORANGE' in line or 'QZCHARGE' in line:
                    if nsteps_value == '':
                        original_inp_lines += line.replace('QZCHARGE', str(net_charge_value)).replace('QZTEMP', str(temp_value)).replace('QZNSTEPS', str(nsteps_value)).replace('QZATMORANGE', str(atom_range))
                    else:
                        original_inp_lines += line.replace('QZCHARGE', str(net_charge_value)).replace('QZTEMP', str(temp_value)).replace('QZNSTEPS', str(int(nsteps_value))).replace('QZATMORANGE', str(atom_range))
                else:
                    original_inp_lines += line

        if os.path.exists(file_path+inp_file):
            os.remove(file_path+inp_file)
        with open(file_path+inp_file, 'w+') as inp_source_file:
            print('file opened ',file_path+inp_file)
            inp_source_file.write(original_inp_lines)
            print('file closed ', file_path + inp_file)
        return True

    except Exception as e:
        print('exception in replacing inp file is ',str(e))
        return False


@csrf_exempt
def TASS_nvt_equilibiration_preparation(user_email_string,inp_command_id,project_id,project_name,command_tool, command_title, user_id='',user_selected_mutation=''):
    group_project_name = get_group_project_name(str(project_id))
    print("inside TASS_nvt_equilibiration_preparation function")
    print("user id is ",user_id)
    status_id = config.CONSTS['status_initiated']
    print("inside TASS_nvt_equilibiration_preparation function")
    print('TASS_simulation_path is')
    file_path = config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + command_tool + '/' + user_selected_mutation + '/'
    print(file_path)

    no_of_thread_key = "TASS_nvt_equilibration_number_of_threads"
    ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=no_of_thread_key).latest(
        'entry_time')

    number_of_threads = int(ProjectToolEssentials_res.key_values)

    temp_key = "TASS_nvt_equilibration_temp_value"
    temp_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=temp_key).latest(
        'entry_time')

    temp_value = float(temp_ProjectToolEssentials_res.key_values)

    nsteps_key = "TASS_nvt_equilibration_nsteps_value"
    nsteps_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=nsteps_key).latest(
        'entry_time')

    nsteps_value = int(nsteps_ProjectToolEssentials_res.key_values)

    print("number of threads is ",number_of_threads)


    source_file_path = file_path
    print('source file path in TASS Equilibration preparation --------------')
    print(source_file_path)
    net_charge_value = ''
    function_returned_value = replace_temp_and_nsteps_in_inp_file(file_path, 'pre_HEAT.in', 'Heat.in', temp_value, nsteps_value,net_charge_value)

    if function_returned_value:
        print('replace inp file function returned true')
        print('slurm value selected is yes')
        initial_string = 'QZW'
        # module_name = 'CatMec'
        module_name = 'TASS'
        # job_name = initial_string + '_' + str(project_name) + '_' + module_name + '_r' + str(md_run_no_of_conformation)
        job_name = str(initial_string) + '_' + module_name
        job_detail_string = module_name + '_NVT_EQUILIBRATION'
        server_value = 'allcpu'
        pre_simulation_script = 'pre_TASS_NVT_equilibration.sh'
        simulation_script = 'TASS_NVT_equilibration_windows_format.sh'
        generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                   number_of_threads, command_title,'')

        print('after generate_slurm_script ************************************************************************')
        print('before changing directory')
        print(os.getcwd())
        print('after changing directory')
        os.chdir(source_file_path)
        print(os.getcwd())
        print("Converting from windows to unix format")
        print("perl -p -e 's/\r$//' < TASS_NVT_equilibration_windows_format.sh > TASS_NVT_equilibration.sh")
        os.system("perl -p -e 's/\r$//' < TASS_NVT_equilibration_windows_format.sh > TASS_NVT_equilibration.sh")
        print('queuing **********************************************************************************')
        cmd = "sbatch "+ source_file_path + "/" + "TASS_NVT_equilibration.sh"
        print("Submitting Job1 with command: %s" % cmd)
        status, jobnum = commands.getstatusoutput(cmd)
        print("job id is ", jobnum)
        print("status is ", status)
        print("job id is ", jobnum)
        print("status is ", status)
        print(jobnum.split())
        lenght_of_split = len(jobnum.split())
        index_value = lenght_of_split - 1
        print(jobnum.split()[index_value])
        job_id = jobnum.split()[index_value]
        # save job id
        job_id_key_name = "job_id"
        entry_time = datetime.now()
        try:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in try of TASS EQUILIBRATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                   project_id=project_id,
                                                                                   entry_time=entry_time,
                                                                                   job_id=job_id,
                                                                                   job_status="1",
                                                                                   job_title=job_name,
                                                                                   job_details=job_detail_string)
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
        except db.OperationalError as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS EQUILIBRATION  SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_name,
                                                                job_details=job_detail_string)
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
            print("saved")
        except Exception as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS EQUILIBRATION  SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("exception is ",str(e))
            pass
            '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                   project_id=project_id,
                                                                                   entry_time=entry_time,
                                                                                   values=job_id,
                                                                                   job_id=job_id)
            QzwSlurmJobDetails_save_job_id.save()
            print("saved")'''
        print('queued')

        return True
    else:
        print('replace inp file function returned False')
        return False\


@csrf_exempt
def TASS_nvt_simulation_preparation(user_email_string,inp_command_id,project_id,project_name,command_tool,command_title,user_id='',user_selected_mutation=''):
    print("inside TASS_nvt_simulation_preparation function")
    group_project_name = get_group_project_name(str(project_id))
    print("user id is ",user_id)
    status_id = config.CONSTS['status_initiated']

    print('TASS_simulation_path is')
    file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + '/' + user_selected_mutation + '/'
    print(file_path)

    try:
        temp_key = "TASS_nvt_simulation_temp_value"
        temp_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=temp_key).latest(
            'entry_time')

        temp_value = float(temp_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print(str(e))
        temp_value = ''
    try:
        no_of_thread_key = "TASS_nvt_equilibration_number_of_threads"
        ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=no_of_thread_key).latest(
            'entry_time')

        number_of_threads = int(ProjectToolEssentials_res.key_values)
    except Exception as e:
        print("exceptio is ",str(e))
        number_of_threads = ''
    try:
        atom_range_key = "TASS_nvt_simulation_qmm_atom_range"
        atom_range_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=atom_range_key).latest(
            'entry_time')

        atom_range_value = str(atom_range_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print("exception is ",str(e))
        atom_range_value = ''

    print("number of threads is ",number_of_threads)

    try:
        nstep_val_key = 'TASS_nvt_simulation_nsteps_value'
        nstep_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=nstep_val_key).latest(
            'entry_time')

        nstep_value = float(nstep_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print(str(e))
        nstep_value = ''
    
    try:
        net_charge_val_key = 'TASS_net_charge'
        net_charge_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=net_charge_val_key).latest(
            'entry_time')

        net_charge_value = net_charge_ProjectToolEssentials_res.key_values
    except Exception as e:
        print(str(e))
        net_charge_value = ''    
    source_file_path = file_path
    print('source file path in TASS NVT Simulation preparation --------------')
    print(source_file_path)
    #function_returned_value = replace_temp_and_nsteps_in_inp_file(file_path, 'pre_test.in', 'test.in', '', '', atom_range_value)
    function_returned_value = replace_temp_and_nsteps_in_inp_file(file_path, 'pre_test.in', 'test.in', temp_value, nstep_value, atom_range_value,net_charge_value)


    if function_returned_value:
        print('replace inp file function returned true')
        print('slurm value selected is yes')
        initial_string = 'QZW'
        module_name = 'TASS'
        job_name = str(initial_string) + '_' + module_name
        job_detail_string = module_name + '_NVT_SIMULATION'
        server_value = 'allcpu'
        pre_simulation_script = 'pre_TASS_NVT_simulation.sh'
        simulation_script = 'TASS_NVT_simulation_windows_format.sh'
        generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                   number_of_threads, command_title,'')

        print('after generate_slurm_script ************************************************************************')
        print('before changing directory')
        print(os.getcwd())
        print('after changing directory')
        os.chdir(source_file_path)
        print(os.getcwd())
        print("Converting from windows to unix format")
        print("perl -p -e 's/\r$//' < TASS_NVT_simulation_windows_format.sh > TASS_NVT_simulation.sh")
        os.system("perl -p -e 's/\r$//' < TASS_NVT_simulation_windows_format.sh > TASS_NVT_simulation.sh")
        print('queuing **********************************************************************************')
        cmd = "sbatch "+ source_file_path + "TASS_NVT_simulation.sh"
        print("Submitting Job1 with command: %s" % cmd)
        status, jobnum = commands.getstatusoutput(cmd)
        print("job id is ", jobnum)
        print("status is ", status)
        print("job id is ", jobnum)
        print("status is ", status)
        print(jobnum.split())
        lenght_of_split = len(jobnum.split())
        index_value = lenght_of_split - 1
        print(jobnum.split()[index_value])
        job_id = jobnum.split()[index_value]
        # save job id
        job_id_key_name = "job_id"
        entry_time = datetime.now()
        try:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in try of TASS SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                   project_id=project_id,
                                                                                   entry_time=entry_time,
                                                                                   job_id=job_id,
                                                                                   job_status="1",
                                                                                   job_title=job_name,
                                                                                   job_details=job_detail_string)
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
            print('saved and queued')
        except db.OperationalError as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_name,
                                                                job_details=job_detail_string)
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
            print("saved")
        except Exception as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("exception is ",str(e))
            pass
            '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                   project_id=project_id,
                                                                                   entry_time=entry_time,
                                                                                   values=job_id,
                                                                                   job_id=job_id)
            QzwSlurmJobDetails_save_job_id.save()
            print("saved")'''
            print('not queued')

        return True
    else:
        print('replace inp file function returned False')
        return False


@csrf_exempt
def TASS_qmm_mm_preparation(user_email_string,inp_command_id,project_id,project_name,command_tool,command_title,user_id='',user_selected_mutation=''):
    group_project_name = get_group_project_name(str(project_id))
    print("inside TASS_qmm_mm_preparation function")
    print("user id is ",user_id)
    status_id = config.CONSTS['status_initiated']

    print("inside TASS_qmm_mm_preparation function")
    print('TASS_simulation_path is')
    file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/' +project_name + '/' + command_tool + '/' + user_selected_mutation + '/'
    print(file_path)

    no_of_thread_key = "TASS_nvt_equilibration_number_of_threads"
    ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=no_of_thread_key).latest(
        'entry_time')

    number_of_threads = int(ProjectToolEssentials_res.key_values)

    collective_range_key = "TASS_collective_filter_json"
    collective_range_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=collective_range_key).latest(
        'entry_time')

    pre_collective_range_value = collective_range_ProjectToolEssentials_res.key_values
    collective_range_value = str(pre_collective_range_value)

    extra_option_key = "TASS_extra_functionality_json"
    extra_option_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=extra_option_key).latest(
        'entry_time')

    pre_extra_option_value = extra_option_ProjectToolEssentials_res.key_values
    extra_option_value = str(pre_extra_option_value)

    print("number of threads is ",number_of_threads)


    source_file_path = file_path
    print('source file path in TASS NVT Simulation preparation --------------')
    print(source_file_path)

    plumed_replacement_completion = False
    try:
        atom_range_key = "TASS_nvt_simulation_qmm_atom_range"
        atom_range_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                          key_name=atom_range_key).latest(
            'entry_time')

        atom_range_value = str(atom_range_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print(str(e))
        atom_range_value = ''
    try:
        temp_key = "TASS_nvt_equilibration_temp_value"
        temp_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=temp_key).latest(
            'entry_time')

        temp_value = float(temp_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print(str(e))
        temp_value = ''
    try:
        nstep_val_key = 'TASS_simulation_nsteps_value'
        nstep_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=nstep_val_key).latest(
            'entry_time')

        nstep_value = float(nstep_ProjectToolEssentials_res.key_values)
    except Exception as e:
        print(str(e))
        nstep_value = ''

    try:
        net_charge_val_key = 'TASS_net_charge'
        net_charge_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                    key_name=net_charge_val_key).latest(
            'entry_time')

        net_charge_value = net_charge_ProjectToolEssentials_res.key_values
    except Exception as e:
        print(str(e))
        net_charge_value = ''

    os.chdir(file_path)

    if os.path.exists(file_path+'plumed.dat'):
        os.remove(file_path+'plumed.dat')

    print('python generate_plumed_file.py "' + collective_range_value + '"' + ' "' + extra_option_value + '" ' + file_path)
    os.system('python generate_plumed_file.py "' + collective_range_value + '"' + ' "' + extra_option_value + '" ' + file_path)

    if os.path.exists(file_path+'plumed.dat'):
        plumed_replacement_completion = True

    function_returned_value = replace_temp_and_nsteps_in_inp_file(file_path, 'pre_md_qmm.in', 'md_qmm.in', temp_value, nstep_value, atom_range_value,net_charge_value)

    if plumed_replacement_completion:
        if function_returned_value:
            print('replace inp file function returned true')
            print('slurm value selected is yes')
            initial_string = 'QZW'
            # module_name = 'CatMec'
            module_name = 'TASS'
            # job_name = initial_string + '_' + str(project_name) + '_' + module_name + '_r' + str(md_run_no_of_conformation)
            job_name = str(initial_string) + '_' + module_name
            job_detail_string = module_name + '_TASS_SIMULATION'
            server_value = 'allcpu'
            pre_simulation_script = 'pre_TASS_simulation.sh'
            simulation_script = 'TASS_simulation_windows_format.sh'
            generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                       number_of_threads, command_title,'')
            generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                       number_of_threads, command_title,'')

            print('after generate_slurm_script ************************************************************************')
            print('before changing directory')
            print(os.getcwd())
            print('after changing directory')
            os.chdir(source_file_path)
            print(os.getcwd())
            print("Converting from windows to unix format")
            print("perl -p -e 's/\r$//' < TASS_simulation_windows_format.sh > TASS_simulation.sh")
            os.system("perl -p -e 's/\r$//' < TASS_simulation_windows_format.sh > TASS_simulation.sh")
            print('queuing **********************************************************************************')
            cmd = "sbatch "+ source_file_path + "/" + "TASS_simulation.sh"
            print("Submitting Job1 with command: %s" % cmd)
            status, jobnum = commands.getstatusoutput(cmd)
            print("job id is ", jobnum)
            print("status is ", status)
            print("job id is ", jobnum)
            print("status is ", status)
            print(jobnum.split())
            lenght_of_split = len(jobnum.split())
            index_value = lenght_of_split - 1
            print(jobnum.split()[index_value])
            job_id = jobnum.split()[index_value]
            # save job id
            job_id_key_name = "job_id"
            entry_time = datetime.now()
            try:
                print(
                    "<<<<<<<<<<<<<<<<<<<<<<< in try of TASS SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                       project_id=project_id,
                                                                                       entry_time=entry_time,
                                                                                       job_id=job_id,
                                                                                       job_status="1",
                                                                                       job_title=job_name,
                                                                                       job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS QMM SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
                print("saved")
            except Exception as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS QMM SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print("exception is ",str(e))
                pass
                '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                       project_id=project_id,
                                                                                       entry_time=entry_time,
                                                                                       values=job_id,
                                                                                       job_id=job_id)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")'''
            print('queued')

            return True
        else:
            print('replace inp file function returned False')
            return False
    else:
        print('replacement in plumed.dat was not successful')
        return False


def queue_slurm_script_of_thermostability(user_id,project_id,file_path,pre_std_file_name,file_name):
    print("inside queue_slurm_script_of_thermostability function")
    print('after generate_slurm_script ************************************************************************')
    print('before changing directory')
    print(os.getcwd())
    print('after changing directory')
    os.chdir(file_path)
    print(os.getcwd())
    print("Converting from windows to unix format")
    print("perl -p -e 's/\r$//' < "+str(file_path)+str(pre_std_file_name)+" > "+str(file_path)+str(file_name))
    os.system("perl -p -e 's/\r$//' < "+str(file_path)+str(pre_std_file_name)+" > "+str(file_path)+str(file_name))
    
    print('queuing **********************************************************************************')
    print("sbatch "+ file_path + "/" + str(file_name))
    #cmd = "srun "+ file_path + "/" + str(file_name)
    cmd = "sbatch " + os.path.join(str(file_path),str(file_name))
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in try of Thermostability JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id,
                                                            job_status="1",
                                                            job_title='qzw_create_mutation',
                                                            job_details='creating mutation')
        QzwSlurmJobDetails_save_job_id.save()
    except db.OperationalError as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of Thermostability  JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id,
                                                            job_status="1",
                                                            job_title='qzw_create_mutation',
                                                            job_details='creating mutation')
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")
    except Exception as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of Thermostability  JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("exception is ",str(e))
        pass
        '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                               project_id=project_id,
                                                                               entry_time=entry_time,
                                                                               values=job_id,
                                                                               job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")'''
    print('queued')
    # return True
    return True,job_id



@csrf_exempt
def plot_energy_preparation(user_email_string, inp_command_id,project_id,project_name,command_tool,command_title,user_id='',user_selected_mutation=''):
    group_project_name = get_group_project_name(str(project_id))
    print("inside plot_energy_preparation function")
    print("user id is ",user_id)
    status_id = config.CONSTS['status_initiated']

    print("inside plot_energy_preparation function")
    print('TASS_simulation_path is')
    file_path = config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + command_tool + '/' + user_selected_mutation + '/'
    print(file_path)

    plot_energy_variable_key = 'plot_energy_variables'
    ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=plot_energy_variable_key).latest(
        'entry_time')

    plot_energy_variable = ProjectToolEssentials_res.key_values
    plot_energy_variable_to_list = eval(plot_energy_variable)
    plot_energy_variable_to_list_len = len(plot_energy_variable_to_list)

    source_file_path = file_path
    print('source file path in TASS NVT Simulation preparation --------------')
    print(source_file_path)

    os.chdir(file_path)

    print('replace inp file function returned true')
    print('slurm value selected is yes')
    initial_string = 'QZW'
    # module_name = 'CatMec'
    module_name = 'TASS'
    # job_name = initial_string + '_' + str(project_name) + '_' + module_name + '_r' + str(md_run_no_of_conformation)
    job_name = str(initial_string) + '_' + module_name
    job_detail_string = module_name + '_PLOT_ENERGY'
    server_value = 'qzyme2'
    print("*******************************************************************")
    print(plot_energy_variable_to_list)
    print(plot_energy_variable_to_list_len)
    print('plumed sum_hills --hills HILLS --kt 2.5 --mintozero --idw ' + str(','.join(plot_energy_variable_to_list)))
    print("*******************************************************************")
    simulation_script = 'plot_energy_windows_format.sh'
    if plot_energy_variable_to_list_len > 1 or plot_energy_variable_to_list_len == 0:
        pre_simulation_script = 'pre_plot_energy_with_multiple_parameter.sh'
        generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                   1, command_title,'')
    elif plot_energy_variable_to_list_len == 1:
        pre_simulation_script = 'pre_plot_energy_with_single_parameter.sh'
        dynamic_Variable_Str = '--idw ' + str(','.join(plot_energy_variable_to_list))
        # plumed_cmd = 'plumed sum_hills --hills HILLS --kt 2.5 --mintozero ' + dynamic_Variable_Str
        plumed_cmd = 'plumed sum_hills --hills HILLS --kt 2.5 --mintozero'
        generate_TASS_slurm_script(file_path, server_value, job_name, pre_simulation_script, simulation_script,
                                1, command_title, plumed_cmd)


    print('after generate_slurm_script ************************************************************************')
    print('before changing directory')
    print(os.getcwd())
    print('after changing directory')
    os.chdir(source_file_path)
    print(os.getcwd())
    print("Converting from windows to unix format")
    print("perl -p -e 's/\r$//' < plot_energy_windows_format.sh > plot_energy.sh")
    os.system("perl -p -e 's/\r$//' < plot_energy_windows_format.sh > plot_energy.sh")
    print('queuing **********************************************************************************')
    cmd = "sbatch "+ source_file_path + "/" + "TASS_simulation.sh"
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in try of TASS PLOT ENERGY JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                               project_id=project_id,
                                                                               entry_time=entry_time,
                                                                               job_id=job_id,
                                                                               job_status="1",
                                                                               job_title=job_name,
                                                                               job_details=job_detail_string)
        QzwSlurmJobDetails_save_job_id.save()
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
    except db.OperationalError as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS PLOT ENERGY JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id,
                                                            job_status="1",
                                                            job_title=job_name,
                                                            job_details=job_detail_string)
        QzwSlurmJobDetails_save_job_id.save()
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title,job_id)
        print("saved")
    except Exception as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of TASS PLOT ENERGY JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("exception is ",str(e))
        pass
        '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                               project_id=project_id,
                                                                               entry_time=entry_time,
                                                                               values=job_id,
                                                                               job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")'''
    print('queued')

    return True



class Preliminary_Studies(APIView):
    def get(self,request):
        pass

    def post(self,request):
        print("INSIDE CLASS Preliminary_Studies")
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        primary_command_runnable = commandDetails_result.primary_command

        database_key_names = ["output_option_key","no_of_thread_key","max_no_of_sequences_key","query_type_name_key","evalue_option_key","preliminary_query_fasta_file_name","preliminary_database_fasta_file_name","max_target_seq"]
        database_values = []
        for key_names in database_key_names:
            try:
                ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,key_name=key_names).latest('entry_time')
                fetched_value_from_db = str(ProjectToolEssentials_res.key_values)
                database_values.append(fetched_value_from_db)
            except Exception as e:
                database_values.append('')
        blastx_string = ''
        if database_values[3] == "prot":
            blastx_string = "/software/usr/ncbi-blast-2.11.0+/bin/blastp"
        elif database_values[3] == "nucl":
            blastx_string = "/software/usr/ncbi-blast-2.11.0+/bin/blastn"
        elif database_values[3] == "mrna":
            blastx_string = "/software/usr/ncbi-blast-2.11.0+/bin/blastx"
        else:blastx_string = "/software/usr/ncbi-blast-2.11.0+/bin/blastx"
        blast_cmd_1 = "/software/usr/ncbi-blast-2.11.0+/bin/makeblastdb -in "+str(database_values[6])+" -dbtype "+str(database_values[3])
        # blast_cmd_2 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out test0.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt '6 qseqid sseqid sseq'"
        # blast_cmd_2 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out test0.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt 4"
        # before review working
        # blast_cmd_2 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out test0.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt '4 qseqid sseqid sseq'"
        # blast_cmd_3 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out out.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt '7 qseqid length qlen slen qstart qend sstart send evalue pident length qcovs '"
        blast_cmd_2 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out test0.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt '4 qseqid sseqid sseq'"
        blast_cmd_3 = "time "+str(blastx_string)+" -query "+str(database_values[5])+" -db "+str(database_values[6])+" -out out.txt -evalue "+str(database_values[4])+" -num_threads "+str(database_values[1])+" -max_target_seqs "+str(database_values[7])+" -outfmt '7 qseqid length qlen slen qstart qend sstart send evalue pident length qcovs '"
        generate_bokeh_aln_file_command = "/usr/bin/python generate_bokeh_aln_file.py '"+str(database_values[5]+"'")
        protein_analysis_computation_script_command = "python generate_protein_analysis_calculations.py "+str(project_id)
        print("protein_analysis_computation_script_command")
        print(protein_analysis_computation_script_command)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print("database_values")
        print(database_values)
        print(blast_cmd_1)
        print(blast_cmd_2)
        print(blast_cmd_3)
        print(generate_bokeh_aln_file_command)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        file_path = config.PATH_CONFIG[
                     'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + commandDetails_result.command_tool + '/' + commandDetails_result.command_title + '/'
        print("file path is ")
        print(file_path)
        new_shell_script_lines = ''

        with open(file_path + 'blast_windows_format.sh' , 'r') as source_file:
            print('inside opening ', file_path + 'blast_windows_format.sh')
            content = source_file.readlines()
            for line in content:
                if 'blast_1_cmd' in line:
                    new_shell_script_lines += (line.replace('blast_1_cmd', str(blast_cmd_1)))
                elif 'blast_2_cmd' in line:
                    new_shell_script_lines += (line.replace('blast_2_cmd', str(blast_cmd_2)))
                elif 'blast_3_cmd' in line:
                    new_shell_script_lines += (line.replace('blast_3_cmd', str(blast_cmd_3)))
                elif 'generate_bokeh_aln_file_command' in line:
                    new_shell_script_lines += (line.replace('generate_bokeh_aln_file_command', str(generate_bokeh_aln_file_command)))
                elif 'protein_analysis_computation_script_command' in line:
                    new_shell_script_lines += (line.replace('protein_analysis_computation_script_command', str(protein_analysis_computation_script_command)))
                elif 'DB_file' in line:
                    new_shell_script_lines += line.replace('DB_file', str(database_values[6])).replace('Query_file', str(database_values[5]))
                elif 'Query_file' in line:
                    new_shell_script_lines += (line.replace('Query_file', str(database_values[5])))
                else:
                    new_shell_script_lines += line
        print("new_shell_script_lines is ")
        print(new_shell_script_lines)
        if os.path.exists(file_path + 'blast_wn_frmt.sh'):
            os.remove(file_path + 'blast_wn_frmt.sh')
        with open(file_path + 'blast_wn_frmt.sh', 'w+')as new_bash_script:
            new_bash_script.write(new_shell_script_lines)

        print('after generate_slurm_script ************************************************************************')
        print('before changing directory')
        print(os.getcwd())
        print('after changing directory')
        os.chdir(file_path)
        print(os.getcwd())
        print("Converting from windows to unix format")
        print("perl -p -e 's/\r$//' < blast_wn_frmt.sh > blast.sh")
        os.system("perl -p -e 's/\r$//' < blast_wn_frmt.sh > blast.sh")

        print('primary_command_runnable')
        print(primary_command_runnable)

        os.chdir(file_path)

        print("dirname")
        print(os.getcwd())

        print("runnable command is")
        print(primary_command_runnable)
        os.chdir(file_path)
        print("working directory after changing CHDIR")
        print(os.system("pwd"))

        #execute command
        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string,project_name,project_id,commandDetails_result.command_tool,commandDetails_result.command_title)
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print("printing status ofprocess")
        print(process_return.returncode)
        print("printing output of process")
        print(out)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+'/'+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< success try block PROTEIN INFORMATION >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< success except block PROTEIN INFORMATION >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< try block PROTEIN INFORMATION >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< error except block PROTEIN INFORMATION >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

def retrieve_project_tool_essentials_values(project_id, key_name):
    print("inside retrieve_project_tool_essentials_values function")
    print(("project_id ",str(project_id)))
    print(("key_name ",key_name))
    try:
        print("inside try of retrieve_project_tool_essentials_values block")
        ProjectToolEssentials_res_value = ProjectToolEssentials.objects.all().filter(project_id=str(project_id),
                                                                                     key_name=key_name).latest(
            'entry_time')
        tool_essential_value = ProjectToolEssentials_res_value.key_values
    except Exception as e:
        print("exception in retrieve_project_tool_essentials_values is ")
        print((str(e)))
        tool_essential_value = ''
    return tool_essential_value


# TASS
class Thermostability(APIView):
    def get(self,request):
        pass

    def post(self,request):
        print("INSIDE CLASS Thermostability")
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = str(QzwProjectDetails_res.project_name)
        group_project_name = get_group_project_name(str(project_id))
        key = 'thermostability_xtc_or_pdb_file'
        pdb_file_names = retrieve_project_tool_essentials_values(project_id, key)
        job_id = ''
        print("type(pdb_file_name)")
        print(type(pdb_file_names))
        if type(pdb_file_names) == list:
            print("HURRRAAAAAAAAAAAAAAYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
            print("type(pdb_file_name) is list")
            print(len(pdb_file_names))
        # for pdb_file_name in pdb_file_names.split(","):
        file_path = config.PATH_CONFIG['shared_folder_path'] + group_project_name + '/' + project_name + '/' + config.PATH_CONFIG['Thermostability_path'] + '/wild_type/'
        qz_workbench_script_path = config.PATH_CONFIG['shared_scripts'] + '/' + config.PATH_CONFIG['Thermostability_path']
        create_mutate_script_path = config.PATH_CONFIG['shared_folder_path'] + group_project_name + '/' + project_name + '/' + config.PATH_CONFIG['Thermostability_path']
        wild_type_foldex_script = ''
        # wild_type_foldex_script = create_mutate_script_path+"/foldx --command=Stability --pdb="+str(pdb_file_name)+" --output-file=test"
        for pdb_file_name in pdb_file_names.split(","):
            wild_type_foldex_script += qz_workbench_script_path+"/foldx --command=Stability --pdb="+str(pdb_file_name)+" --output-file="+pdb_file_name[:-4]+"\n"
        primary_command_runnable = commandDetails_result.primary_command
        destination_file_path = file_path
        source_file_path = config.PATH_CONFIG['shared_folder_path'] + group_project_name + '/' + project_name + '/' + config.PATH_CONFIG['Designer_path']
        try:
            print("inside try")
            ""
            shutil.copyfile(os.path.join(qz_workbench_script_path,"create_mutation.py"),os.path.join(destination_file_path,"create_mutation.py"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"pymol_mutate.py"),os.path.join(destination_file_path,"pymol_mutate.py"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"matrix_generation.py"),os.path.join(destination_file_path,"matrix_generation.py"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"create_mutate_std.sh"),os.path.join(destination_file_path,"create_mutate_std.sh"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"check_progress_and_view_graph.py"),os.path.join(destination_file_path,"check_progress_and_view_graph.py"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"rotabase.txt"),os.path.join(destination_file_path,"rotabase.txt"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"generate_mean_variant_plot.py"),os.path.join(destination_file_path,"generate_mean_variant_plot.py"))
            shutil.copyfile(os.path.join(qz_workbench_script_path,"generate_energy_plot.py"),os.path.join(destination_file_path,"generate_energy_plot.py"))
        except Exception as e:
            print(('exception in copying file of mutation is ', str(e)))
            pass

        if commandDetails_result.command_title == "create_mutation":
            primary_command_runnable = primary_command_runnable
            print(file_path)
            std_script = 'create_mutate_std.sh'
            #QZ_MUTATE_SCRIPT
            mutate_win_script = 'create_mutate_windows.sh'
            mutate_script = 'create_mutate.sh'
            new_shell_script_lines = ''
            server_name = 'allcpu'
            initial_string = 'QZW'
            module_name = 'Thermostability_mutation'
            job_name = initial_string + '_' + str(project_id) + '_' + project_name + '_' + '_' + module_name
            number_of_threads = 4
            print('before opening ', file_path + '/' + std_script)
            with open(file_path + '/' + std_script, 'r') as source_file:
                print('inside opening ', file_path + '/' + std_script)
                content = source_file.readlines()
                for line in content:
                    if 'QZSERVER' in line:
                        new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
                    elif 'QZJOBNAME' in line:
                        new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
                    elif 'QZTHREADS' in line:
                        new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
                    elif 'QZ_MUTATE_SCRIPT' in line:
                        new_shell_script_lines += (line.replace('QZ_MUTATE_SCRIPT', str(primary_command_runnable)))
                    elif 'QZ_PROJECT_ID' in line or 'QZ_MUTATION_FILE' in line:
                        # new_shell_script_lines += (line.replace('QZ_PROJECT_ID', str(project_id)))
                        new_shell_script_lines += line.replace('QZ_PROJECT_ID', str(project_id)).replace('QZ_MUTATION_FILE', str(project_name+'_mutate.txt'))
                    # elif 'QZ_MUTATION_FILE' in line:
                    #     new_shell_script_lines += (line.replace('QZ_MUTATION_FILE', str(project_name+'_mutate.txt')))
                    elif 'wild_type_foldex_script' in line:
                        new_shell_script_lines += (line.replace('wild_type_foldex_script', str(wild_type_foldex_script)))
                    else:
                        new_shell_script_lines += line
            if os.path.exists(os.path.join(file_path,mutate_win_script)):
                print('removing ', file_path + mutate_win_script)
                os.remove(os.path.join(file_path,mutate_win_script))
            # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
            print("************************************************************")
            print("************************************************************")
            print(new_shell_script_lines)
            print("************************************************************")
            print("************************************************************")
            with open(file_path + '/' + mutate_win_script, 'w+')as new_bash_script:
                print("openened "+file_path + '/' + mutate_win_script)
                new_bash_script.write(new_shell_script_lines + "\n")
                print("wrote")
            with open(file_path + '/' + mutate_win_script)as new_bash_script:
                for line in new_bash_script.readlines():
                    print(line)
            #queue_slurm_script_of_thermostability(user_id,project_id,file_path,mutate_win_script,mutate_script)
            submitted_job_boolean_val,job_id = queue_slurm_script_of_thermostability(user_id,project_id,file_path,mutate_win_script,mutate_script)
            # queue_slurm_script_of_thermostability(user_id,project_id,file_path,mutate_win_script,mutate_script)
            #inp_command_id = job_id
            #job_id = inp_command_id
            # primary_command_runnable = 'sh create_mutate.sh'
            primary_command_runnable = ''
            #primary_command_runnable = ''

        print('primary_command_runnable')
        print(primary_command_runnable)

        os.chdir(file_path)

        print("dirname")
        print(os.getcwd())

        print("runnable command is")
        print(primary_command_runnable)
        os.chdir(file_path)
        print("working directory after changing CHDIR")
        print(os.system("pwd"))

        #execute command

        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title,job_id)
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print("printing status ofprocess")
        print(process_return.returncode)
        print("printing output of process")
        print(out)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+'/'+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< success try block Thermostability >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< success except block Thermostability >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< try block Thermostability >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< error except block Thermostability  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)

            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


# TASS
class TASS(APIView):
    def get(self,request):
        pass

    def post(self,request):
        print("INSIDE CLASS TASS")
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        primary_command_runnable = commandDetails_result.primary_command
        primary_command_runnable = re.sub('sh amber_nvt_equilibrzation.sh', '', primary_command_runnable)
        primary_command_runnable = re.sub('sh amber_nvt_equilibration.sh', '', primary_command_runnable)
        primary_command_runnable = re.sub('sh amber_nvt_simulation.sh', '', primary_command_runnable)
        primary_command_runnable = re.sub('sh TASS_simulation.sh', '', primary_command_runnable)

        user_mutation_selection_key_name = 'TASS_mutation_selection'

        #get list of index file options for gmx input
        ProjectToolEssentials_res_mutation_selection = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=user_mutation_selection_key_name).latest('entry_time')
        user_selected_mutation = str(ProjectToolEssentials_res_mutation_selection.key_values[1:-1].strip("'"))

        if commandDetails_result.command_title == "gromacs_to_amber":

            file_path = config.PATH_CONFIG[
                            'local_shared_folder_path'] + group_project_name + '/' + project_name + '/' + str(commandDetails_result.command_tool) + '/' + user_selected_mutation + '/'
            print(file_path)
            pre_conv_script = 'pre_conv.sh'
            conv_script = 'conv.sh'
            new_shell_script_lines = ''
            print('before opening ', file_path + '/' + pre_conv_script)
            with open(file_path + '/' + pre_conv_script, 'r') as source_file:
                print('inside opening ', file_path + '/' + pre_conv_script)
                content = source_file.readlines()
                for line in content:
                    if 'QZ_CONV_SCRIPT' in line:
                        new_shell_script_lines += (line.replace('QZ_CONV_SCRIPT', str(primary_command_runnable)))
                    else:
                        new_shell_script_lines += line
            if os.path.exists(file_path + '/' + conv_script):
                print('removing ', file_path + conv_script)
                os.remove(file_path + '/' + conv_script)
            # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
            with open(file_path + '/' + conv_script, 'w+')as new_bash_script:
                new_bash_script.write(new_shell_script_lines + "\n")
            primary_command_runnable = re.sub(primary_command_runnable, 'sh conv.sh', primary_command_runnable)

        elif commandDetails_result.command_title == "nvt_equilibration":
            returned_preparation_value = TASS_nvt_equilibiration_preparation(user_email_string,inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title,commandDetails_result.user_id,user_selected_mutation)
        elif commandDetails_result.command_title == "nvt_simulation":
            returned_preparation_value = TASS_nvt_simulation_preparation(user_email_string,inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title,commandDetails_result.user_id,user_selected_mutation)
        elif commandDetails_result.command_title == "TASS_qmm_mm":
            returned_preparation_value = TASS_qmm_mm_preparation(user_email_string,inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title,commandDetails_result.user_id,user_selected_mutation)
        elif commandDetails_result.command_title == "plot_energy":
            returned_preparation_value = plot_energy_preparation(user_email_string,inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title,commandDetails_result.user_id,user_selected_mutation)

        print('primary_command_runnable')
        print(primary_command_runnable)

        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + commandDetails_result.command_tool + '/' + user_selected_mutation + '/')

        print("dirname")
        print(os.getcwd())

        print("runnable command is")
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + commandDetails_result.command_tool + '/' + user_selected_mutation + '/')
        print("working directory after changing CHDIR")
        print(os.system("pwd"))

        #execute command

        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print("printing status ofprocess")
        print(process_return.returncode)
        print("printing output of process")
        print(out)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+'/'+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< success try block TASS >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< success except block TASS >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< try block TASS >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< error except block TASS  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#analyse_mmpsa
class analyse_mmpbsa(APIView):
    def get(self,request):
        pass


    def post(self,request):
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))

        key_name_indexfile_input = 'mmpbsa_index_file_dict'

        #get list of index file options for gmx input
        ProjectToolEssentials_res_indexfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_indexfile_input).latest('entry_time')

        #get list of .XTC files from different MD runs to execute "gmx trjcat " command
        key_name_xtcfile_input = 'mmpbsa_md_xtc_file_list'

        ProjectToolEssentials_res_xtcfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_xtcfile_input).latest('entry_time')

        #get .tpr file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_tpr_file = 'mmpbsa_tpr_file'

        ProjectToolEssentials_res_tpr_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_tpr_file).latest('entry_time')
        md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.key_values.replace('\\', '/')

        # get .ndx file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_ndx_file = 'mmpbsa_index_file'

        ProjectToolEssentials_res_ndx_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ndx_file).latest('entry_time')
        md_simulations_ndx_file = ProjectToolEssentials_res_ndx_file_input.key_values.replace('\\', '/')

        key_name_CatMec_input = 'substrate_input'
        command_tootl_title = "CatMec"
        # get list of ligand inputs
        ProjectToolEssentials_res_CatMec_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                       key_name=key_name_CatMec_input).latest('entry_time')
        CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.key_values)
        # if User has only one ligand as input
        multiple_ligand_input = False
        if len(CatMec_input_dict) > 1:
            multiple_ligand_input = True

        indexfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_indexfile_input.key_values)
        xtcfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_xtcfile_input.key_values)

        '''
                                                                  .                o8o                         .        
                                                        .o8                `"'                       .o8        
         .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .oooo.   .o888oo      
        888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 `P  )88b    888        
        888   888   888   888   888     Y888'           888    888         888 888        .oP"888    888        
        `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 d8(  888    888 .      
        `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y888""8o   "888"      
        d"     YD                                                          888                                  
        "Y88888P'                                                      .o. 88P                                  
                                                                       `Y888P                                           
        '''
        #if len(xtcfile_input_dict) > 1:
        md_xtc_files_str = ""
        #mmpbsa_project_path
        for xtcfile_inputkey, xtcfile_inputvalue in xtcfile_input_dict.iteritems():
            xtcfile_inputvalue_formatted = xtcfile_inputvalue.replace('\\', '/')
            md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + \
                                config.PATH_CONFIG['md_simulations_path'] + xtcfile_inputvalue_formatted + " "
        gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + config.PATH_CONFIG[
                             'mmpbsa_project_path'] + "merged.xtc -keeplast -cat"
        os.system(gmx_trjcat_cmd)

        '''
                                                                                          oooo                                                .o8              
                                                                                  `888                                               "888              
         .oooooooo ooo. .oo.  .oo.   oooo    ooo      ooo. .oo.  .oo.    .oooo.    888  oooo   .ooooo.              ooo. .oo.    .oooo888  oooo    ooo 
        888' `88b  `888P"Y88bP"Y88b   `88b..8P'       `888P"Y88bP"Y88b  `P  )88b   888 .8P'   d88' `88b             `888P"Y88b  d88' `888   `88b..8P'  
        888   888   888   888   888     Y888'          888   888   888   .oP"888   888888.    888ooo888              888   888  888   888     Y888'    
        `88bod8P'   888   888   888   .o8"'88b         888   888   888  d8(  888   888 `88b.  888    .o              888   888  888   888   .o8"'88b   
        `8oooooo.  o888o o888o o888o o88'   888o      o888o o888o o888o `Y888""8o o888o o888o `Y8bod8P' ooooooooooo o888o o888o `Y8bod88P" o88'   888o 
        d"     YD                                                                                                                                      
        "Y88888P'                                                                                                                                      
        '''
        if multiple_ligand_input:
            ligand_name_input = ""
            #for multiple ligand input
            print("for multiple ligand input")
            #get user input ligand name from DB
            key_name_ligand_input = 'mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.key_values
            #extract ligand number
            if "[ " + ligand_name + " ]" in indexfile_input_dict.keys():
                ligand_name_input = str(indexfile_input_dict["[ "+ligand_name+" ]"])
            indexfile_complex_option_input = ""
            indexfile_receptor_option_input = ""
            #prepare receptor option input string
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name_split = ligand_inputvalue.split("_")
                dict_ligand_name = ligand_name_split[0]
                if "[ "+dict_ligand_name+" ]" in indexfile_input_dict.keys() and dict_ligand_name != ligand_name:
                    indexfile_receptor_option_input += str(indexfile_input_dict["[ "+dict_ligand_name+" ]"]) +" | "
             #prepare complex option input string
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name_split = ligand_inputvalue.split("_")
                dict_ligand_name = ligand_name_split[0]
                if "[ "+dict_ligand_name+" ]" in indexfile_input_dict.keys():
                    indexfile_complex_option_input += str(indexfile_input_dict["[ "+dict_ligand_name+" ]"]) +" | "

            if "[ Protein ]" in indexfile_input_dict.keys():
                indexfile_complex_option_input += str(indexfile_input_dict["[ Protein ]"])
                indexfile_receptor_option_input += str(indexfile_input_dict["[ Protein ]"])
            #reverse the strings
            indexfile_complex_option_input = indexfile_complex_option_input.split(" | ")
            indexfile_complex_option_input = indexfile_complex_option_input[-1::-1]
            reversed_indexfile_complex_option_input = ' | '.join(indexfile_complex_option_input)

            indexfile_receptor_option_input = indexfile_receptor_option_input.split(" | ")
            indexfile_receptor_option_input = indexfile_receptor_option_input[-1::-1]
            reversed_indexfile_receptor_option_input = ' | '.join(indexfile_receptor_option_input)
            print(reversed_indexfile_complex_option_input)
            print(reversed_indexfile_receptor_option_input)
            maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
            protien_ligand_complex_index = receptor_index + 1
            #write protien ligand complex index number to DB
            entry_time = datetime.now()
            key_name_protien_ligand_complex_index = 'mmpbsa_index_file_protien_ligand_complex_number'
            ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(tool_title=commandDetails_result.command_tool,
                                                                                      project_id=project_id,
                                                                                      key_name=key_name_protien_ligand_complex_index,
                                                                                      key_values=protien_ligand_complex_index,
                                                                                      entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            ligand_name_index = protien_ligand_complex_index + 1
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                               'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                                               'md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(
                str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(reversed_indexfile_complex_option_input) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n"+str(ligand_name_input)+"\nname "+str(ligand_name_index)+" ligand"+ "\nq\n")
            file_gmx_make_ndx_input.close()

            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + config.PATH_CONFIG[
                               'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + "gmx_make_ndx_input.txt"
            print(" make index command")
            print(gmx_make_ndx)
            os.system(gmx_make_ndx)

        else:
            #for single ligand input
            #get ligand name
            ligand_name = ""
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name = ligand_inputvalue.split("_")[0]
            #prepare input file for gmx make_ndx command
            protein_index = 0
            ligandname_index = 0
            for indexfile_inputkey, indexfile_inputvalue in indexfile_input_dict.iteritems(): # key is index option text and value is index number
                if ligand_name in indexfile_inputkey:
                    ligandname_index = indexfile_inputvalue
                if "[ Protein ]" == indexfile_inputkey:
                    protein_index = indexfile_inputvalue
            maximum_key_ndx_input = max(indexfile_input_dict,key=indexfile_input_dict.get)
            #print indexfile_input_dict[maximum_key_ndx_input]
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] +1
            protien_ligand_complex_index = receptor_index + 1
            ligand_name_index = protien_ligand_complex_index + 1
            entry_time = datetime.now()
            key_name_protien_ligand_complex_index = 'mmpbsa_index_file_protien_ligand_complex_number'
            ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(
                tool_title=commandDetails_result.command_tool,
                project_id=project_id,
                key_name=key_name_protien_ligand_complex_index,
                key_values=protien_ligand_complex_index,
                entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                              'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                                              'md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(str(protein_index)+"\nname "+str(receptor_index)+" receptor\n"+str(protein_index)+" | "+str(ligandname_index)+"\nname "+str(protien_ligand_complex_index)+" complex"+"\n" +str(ligandname_index)+"\nname "+str(ligand_name_index)+" ligand"+"\nq\n")
            file_gmx_make_ndx_input.close()
            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + config.PATH_CONFIG[
                               'mmpbsa_project_path'] + "complex_index.ndx <"+config.PATH_CONFIG[
                                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                                              'md_simulations_path'] + "gmx_make_ndx_input.txt"

            print(" make index command")
            print(gmx_make_ndx)
            os.system(gmx_make_ndx)

        perform_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file)
        print("perform_cmd_trajconv def>>>>>>>>>>>>>>>>>")
        print("md_simulations_tpr_file")
        print(md_simulations_tpr_file)
        #===================   post processing after make index  ===============================
        # copy MD .tpr file to MMPBSA working directory
        source_tpr_md_file = config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                                 'md_simulations_path'] + md_simulations_tpr_file
        print("source_tpr_md_file")
        print(source_tpr_md_file)
        tpr_file_split = md_simulations_tpr_file.split("/")
        dest_tpr_md_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                           config.PATH_CONFIG['mmpbsa_project_path'] + tpr_file_split[1]
        print("dest_tpr_md_file")
        print(dest_tpr_md_file)
        shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

        # copy topology file from MS to MMPBSA working directory
        source_topology_file = config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                                   'md_simulations_path'] + tpr_file_split[0] + "/topol.top"
        dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                             config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top"
        shutil.copyfile(source_topology_file, dest_topology_file)

        # copy ligand .itp files
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            source_itp_file = config.PATH_CONFIG[
                                  'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + config.PATH_CONFIG[
                                  'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
            dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path'] + ligand_name_split[0] + ".itp"
            shutil.copyfile(source_itp_file, dest_itp_file)

        #copy atom_types.itp file from MD dir
        source_atomtype_itp_file = config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + "atomtypes" + ".itp"
        dest_atomtype_itp_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "atomtypes" + ".itp"
        shutil.copyfile(source_atomtype_itp_file, dest_atomtype_itp_file)

        key_name_ligand_input = 'mmpbsa_input_ligand'
        # processing itp files
        pre_process_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input)

        # ----------------------   make a "trail" directory for MMPBSA   -----------------------
        os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial")
        # copying MMPBSA input files to trail directory
        # copy .XTC file
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "merged-recentered.xtc",
                        config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.xtc")

        # copy other input files for MMPBSA
        for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path']):
            # copy .TPR file
            if file_name.endswith(".tpr"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.tpr")
            # copy .NDX file
            if file_name.endswith(".ndx"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/index.ndx")

            # copy .TOP file
            if file_name.endswith(".top"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+ '/'+project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/"+file_name)
            # copy .ITP files
            if file_name.endswith(".itp"):
                #check for multiple ligand
                if multiple_ligand_input:
                    #for multiple ligand
                    # renaming user input ligand as LIGAND
                    key_name_ligand_input = 'mmpbsa_input_ligand'

                    ProjectToolEssentials_res_ligand_input = \
                        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                   key_name=key_name_ligand_input).latest('entry_time')
                    ligand_name = ProjectToolEssentials_res_ligand_input.key_values
                else:
                    #for single ligand
                    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                        ligand_name = ligand_inputvalue.split("_")[0]
                if file_name[:-4] == ligand_name:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+ project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/ligand.itp")
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/"+file_name)
                else:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)
        # ----------------   re-creating topology file   -------------------------
        topology_contents_part1 = ""
        topology_contents_part2 = ""
        topology_contents_part3 = ""
        topology_content_filtered =""
        topology_file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                             config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top"

        # get topology file [ molecules ] section contents
        with open(topology_file_path) as topol_file:
            for line_topol in topol_file:
                topology_contents_part1 += line_topol
                if line_topol.strip() == '[ moleculetype ]':
                    break

        # get topology file itp section
        with open(topology_file_path) as topol_file:
            for line in topol_file:
                if line.strip() == '; Include Position restraint file':  # Or whatever test is needed
                    break
            # Reads text until the end of the block:
            for line in topol_file:  # This keeps reading the file
                topology_contents_part2 += line  # Line is extracted (or block_of_lines.append(line), etc.)
        topology_content_filtered = '\n'.join(topology_contents_part1.split('\n')[:-2])

        ligand_itp_exists = True  # for more than one ligand
        for line_seg in topology_contents_part2.split("\n"):
            if re.match('^#include\s*\".*\.itp\"', line_seg):
                if any(ligand_inputvalue.split("_")[0] in line_seg for ligand_inputkey, ligand_inputvalue in
                       CatMec_input_dict.iteritems()):
                    if ligand_itp_exists == False:
                        pass
                    else:
                        topology_contents_part3 += '#include "complex.itp" ' + '\n'
                        topology_contents_part3 += '#include "ligand.itp" ' + '\n'
                        ligand_itp_exists = False
                else:
                    topology_contents_part3 += line_seg + '\n'
            else:
                topology_contents_part3 += line_seg + '\n'

        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol_original.top", "w+") as new_topol:
            new_topol.write(topology_content_filtered + topology_contents_part3)
        # renaming topology file
        os.rename(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top",
                  config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial/backup_topology.txt"
                  )
        os.rename(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol_original.top",
                  config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top"
                  )
        # ----------------   END of re-creating topology file   -------------------------


        '''os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'])

        os.system("sh "+config.PATH_CONFIG['GMX_run_file_one'])
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                 config.PATH_CONFIG['mmpbsa_project_path'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                 config.PATH_CONFIG['mmpbsa_project_path'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])'''
        shared_dir_path = config.PATH_CONFIG['local_shared_folder_path']
        mmpbsa_project_path = config.PATH_CONFIG['mmpbsa_project_path']
        server_name = 'allcpu'
        job_title = "QZW_"+project_id+"_MMPBSA"
        # =======================  get user input threads  ============================
        try:
            key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
            ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_mmpbsa_threads_input).latest('entry_time')
            mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
        except db.OperationalError as e:
            db.close_old_connections()
            key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
            ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_mmpbsa_threads_input).latest('entry_time')
            mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
        # ======================= End of get user input threads  ======================
        prepare_mmpbsa_slurm_script(project_id, shared_dir_path,mmpbsa_project_path,project_name,server_name,job_title,mmpbsa_threads_input)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                 config.PATH_CONFIG['mmpbsa_project_path'])
        slurm_batch_script_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                 config.PATH_CONFIG['mmpbsa_project_path']
        cmd = "sbatch " + slurm_batch_script_path + "/" + "mmpbsa_batch.sh"
        status, jobnum = commands.getstatusoutput(cmd)
        lenght_of_split = len(jobnum.split())
        index_value = lenght_of_split - 1
        print(jobnum.split()[index_value])
        job_id = jobnum.split()[index_value]
        # save job id
        entry_time = datetime.now()
        try:
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_title,
                                                                job_details="CatMec analysis")
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
        except db.OperationalError as e:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in except of CatMec MMPBSA SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_title,
                                                                job_details="CatMec analysis")
            QzwSlurmJobDetails_save_job_id.save()
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
        except Exception as e:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in except of CatMec MMPBSA SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("exception is ", str(e))
            pass
        #update command status to database
        try:
            print("<<<<<<<<<<<<<<<<<<<<<<< error try block CatMec MMPBSA >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            status_id = config.CONSTS['status_success']

            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
        except db.OperationalError as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< error except block CatMec MMPBSA   >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
        return JsonResponse({"success": True})



# execute Designer MMPBSA with job Scheduler
def designer_slurm_queue_analyse_mmpbsa(inp_command_id, md_mutation_folder, project_name, command_tool, project_id,user_id,slurm_job_id):
    group_project_name = get_group_project_name(str(project_id))
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis")
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA/")
    #copy python processing file for mmpbsa

    shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Designer/designer_mmpbsa__slurm_pre_processing.py',config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/designer_mmpbsa__slurm_pre_processing.py")
    shutil.copyfile(config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/designer_mmpbsa__slurm_pre_processing.py", config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA/designer_mmpbsa__slurm_pre_processing.py")
    # Designer MMPBSA with SLURM
    # =======   get assigned server for project ============
    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values
    initial_string = 'QZW'
    module_name = 'Designer_mmpbsa_preperation_'
    job_name = initial_string + '_' + str(
        project_id) + '_' + project_name + '_' + 'mutation_' + md_mutation_folder + '_' + module_name
    dest_file_path =config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool
    number_of_threads =1
    generate_designer_slurm_script(dest_file_path, server_value, job_name, number_of_threads,inp_command_id,md_mutation_folder,project_name,command_tool,project_id,user_id)

    #basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    #windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'

    print("Converting from windows to unix format")
    os.system("perl -p -e 's/\r$//' < "+config.PATH_CONFIG[
        'local_shared_folder_path'] + group_project_name+'/'+project_name + "/" + command_tool + "/"+"basic_sbatch_script_windows_format.sh > "+config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA/"+"designer_sbatch.sh")
    print('queuing **********************************************************************************')

    cmd = "sbatch --dependency=afterok:"+slurm_job_id+" " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA" + "/" + "designer_sbatch.sh"
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
    except db.OperationalError as e:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in except of MMPBSA SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")
    return job_id

#new code for Designer MMPBSA
def designer_queue_analyse_mmpbsa(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    #if Mysql has timed out
    db.close_old_connections()
    print("requst is ----")
    print(request)
    print("md_mutation_folder")
    print(md_mutation_folder)
    entry_time = datetime.now()
    # get command details from database
    #create ANALYSIS and MMPBSA folder in Mutations respective folder
    os.system("mkdir "+config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" +command_tool + "/" +md_mutation_folder+"/Analysis")
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA/")
    inp_command_id = request.POST.get("command_id")
    try:
        print("in designer_queue_analyse_mmpbsa try first DB operation")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
    except db.OperationalError as e:
        print("in designer_queue_analyse_mmpbsa except first DB operation")
        db.close_old_connections()
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)

    project_id = commandDetails_result.project_id
    QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
    project_name = QzwProjectDetails_res.project_name

    mdsimulations_source = config.PATH_CONFIG['shared_folder_path'
                           ] + group_project_name + '/' + project_name + '/' + command_tool + "/"+md_mutation_folder +"/"
    xtc_files_list = {}
    index_file_list = []
    tpr_file_list = []
    xtc_file_list_count = 1
    # loop thru al files and directories in MDSimulations directory
    for dirs in listdir(mdsimulations_source):
        if os.path.isdir(os.path.join(mdsimulations_source, dirs)):  # check if directory
            if re.match("md_run*", dirs):  # considerning only directories starting with md_run
                for dir_files in listdir(os.path.join(mdsimulations_source, dirs)):
                    if dir_files.endswith(".tpr"):  # applying .tpr file filter
                        tpr_file_list.append(os.path.join(dirs, dir_files))
                    if dir_files.endswith(".ndx"):  # applying .ndx file filter
                        index_file_list.append(os.path.join(dirs, dir_files))
                    if dir_files.endswith(".xtc"):  # applying .xtc file filter
                        print("xtc file found")
                        xtc_files_list.update({xtc_file_list_count: os.path.join(dirs, dir_files)})
                        xtc_file_list_count += 1

    ndx_count = 0
    ndx_input_dict = {}
    #
    print(tpr_file_list)
    with open(mdsimulations_source + index_file_list[0], 'r'
              ) as fp:
        lines = fp.readlines()
        for line in lines:
            if re.match("^\[.*\]\n", line):
                ndx_input_dict.update({line.strip(): ndx_count})
                ndx_count += 1

    md_simulations_tpr_file = tpr_file_list[0].replace('\\', '/')

    md_simulations_ndx_file = index_file_list[0].replace('\\', '/')

    # save tpr file required to process MMPBSA in webservices
    key_name_tpr_file = 'designer_mmpbsa_tpr_file'
    ProjectToolEssentials_save_designer_mmpbsa_tpr_file = ProjectToolEssentials(tool_title=command_tool,
                                                                                project_id=project_id,
                                                                                key_name=key_name_tpr_file,
                                                                                key_values=tpr_file_list[0],
                                                                                entry_time=entry_time)
    result_ProjectToolEssentials_save_mmpbsa_tpr_file = ProjectToolEssentials_save_designer_mmpbsa_tpr_file.save()

    key_name_CatMec_input = 'substrate_input'
    command_tootl_title = "CatMec"
    # get list of ligand inputs
    ProjectToolEssentials_res_CatMec_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                   key_name=key_name_CatMec_input).latest('entry_time')
    CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.key_values)
    # if User has only one ligand as input
    multiple_ligand_input = False
    if len(CatMec_input_dict) > 1:
        multiple_ligand_input = True

    indexfile_input_dict = ndx_input_dict
    xtcfile_input_dict = xtc_files_list

    '''
                                                              .                o8o                         .        
                                                    .o8                `"'                       .o8        
     .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .oooo.   .o888oo      
    888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 `P  )88b    888        
    888   888   888   888   888     Y888'           888    888         888 888        .oP"888    888        
    `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 d8(  888    888 .      
    `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y888""8o   "888"      
    d"     YD                                                          888                                  
    "Y88888P'                                                      .o. 88P                                  
                                                                   `Y888P                                           
    '''
    # if len(xtcfile_input_dict) > 1:
    md_xtc_files_str = ""
    # mmpbsa_project_path
    for xtcfile_inputkey, xtcfile_inputvalue in xtcfile_input_dict.iteritems():
        xtcfile_inputvalue_formatted = xtcfile_inputvalue.replace('\\', '/')
        md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + \
                            command_tool + "/" + md_mutation_folder+ "/" + xtcfile_inputvalue_formatted + " "
    gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
        'local_shared_folder_path'] + group_project_name+'/'+project_name + "/" +command_tool + "/" +md_mutation_folder+"/"+ config.PATH_CONFIG[
                         'mmpbsa_project_path'] + "merged.xtc -keeplast -cat"
    os.system(gmx_trjcat_cmd)

    '''
                                                                                      oooo                                                .o8              
                                                                              `888                                               "888              
     .oooooooo ooo. .oo.  .oo.   oooo    ooo      ooo. .oo.  .oo.    .oooo.    888  oooo   .ooooo.              ooo. .oo.    .oooo888  oooo    ooo 
    888' `88b  `888P"Y88bP"Y88b   `88b..8P'       `888P"Y88bP"Y88b  `P  )88b   888 .8P'   d88' `88b             `888P"Y88b  d88' `888   `88b..8P'  
    888   888   888   888   888     Y888'          888   888   888   .oP"888   888888.    888ooo888              888   888  888   888     Y888'    
    `88bod8P'   888   888   888   .o8"'88b         888   888   888  d8(  888   888 `88b.  888    .o              888   888  888   888   .o8"'88b   
    `8oooooo.  o888o o888o o888o o88'   888o      o888o o888o o888o `Y888""8o o888o o888o `Y8bod8P' ooooooooooo o888o o888o `Y8bod88P" o88'   888o 
    d"     YD                                                                                                                                      
    "Y88888P'                                                                                                                                      
    '''
    if multiple_ligand_input:
        ligand_name_input = ""
        # for multiple ligand input
        print("for multiple ligand input")
        # get user input ligand name from DB
        key_name_ligand_input = 'mmpbsa_input_ligand'

        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.key_values
        # extract ligand number
        if "[ " + ligand_name + " ]" in indexfile_input_dict.keys():
            ligand_name_input = str(indexfile_input_dict["[ " + ligand_name + " ]"])
        indexfile_complex_option_input = ""
        indexfile_receptor_option_input = ""
        # prepare receptor option input string
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            dict_ligand_name = ligand_name_split[0]
            if "[ " + dict_ligand_name + " ]" in indexfile_input_dict.keys() and dict_ligand_name != ligand_name:
                indexfile_receptor_option_input += str(indexfile_input_dict["[ " + dict_ligand_name + " ]"]) + " | "
        # prepare complex option input string
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            dict_ligand_name = ligand_name_split[0]
            if "[ " + dict_ligand_name + " ]" in indexfile_input_dict.keys():
                indexfile_complex_option_input += str(indexfile_input_dict["[ " + dict_ligand_name + " ]"]) + " | "

        if "[ Protein ]" in indexfile_input_dict.keys():
            indexfile_complex_option_input += str(indexfile_input_dict["[ Protein ]"])
            indexfile_receptor_option_input += str(indexfile_input_dict["[ Protein ]"])
        # reverse the strings
        indexfile_complex_option_input = indexfile_complex_option_input.split(" | ")
        indexfile_complex_option_input = indexfile_complex_option_input[-1::-1]
        reversed_indexfile_complex_option_input = ' | '.join(indexfile_complex_option_input)

        indexfile_receptor_option_input = indexfile_receptor_option_input.split(" | ")
        indexfile_receptor_option_input = indexfile_receptor_option_input[-1::-1]
        reversed_indexfile_receptor_option_input = ' | '.join(indexfile_receptor_option_input)
        print(reversed_indexfile_complex_option_input)
        print(reversed_indexfile_receptor_option_input)
        maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
        receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
        protien_ligand_complex_index = receptor_index + 1
        # write protien ligand complex index number to DB
        entry_time = datetime.now()
        key_name_protien_ligand_complex_index = 'mmpbsa_index_file_protien_ligand_complex_number'
        ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(
            tool_title=commandDetails_result.command_tool,
            project_id=project_id,
            key_name=key_name_protien_ligand_complex_index,
            key_values=protien_ligand_complex_index,
            entry_time=entry_time)
        result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
        ligand_name_index = protien_ligand_complex_index + 1
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + command_tool+"/"+md_mutation_folder +"/"+ "gmx_make_ndx_input.txt", "w")
        file_gmx_make_ndx_input.write(
            str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(
                reversed_indexfile_complex_option_input) + "\nname " + str(
                protien_ligand_complex_index) + " complex" + "\n" + str(ligand_name_input) + "\nname " + str(
                ligand_name_index) + " ligand" + "\nq\n")
        file_gmx_make_ndx_input.close()

        gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -n " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + command_tool + '/' + md_mutation_folder + "/" + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + command_tool + "/" + md_mutation_folder + '/' + \
                       config.PATH_CONFIG[
                           'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_make_ndx_input.txt"

        print(" make index command")
        print(gmx_make_ndx)
        os.system(gmx_make_ndx)

    else:
        # for single ligand input
        # get ligand name
        ligand_name = ""
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name = ligand_inputvalue.split("_")[0]
        # prepare input file for gmx make_ndx command
        protein_index = 0
        ligandname_index = 0
        for indexfile_inputkey, indexfile_inputvalue in indexfile_input_dict.iteritems():  # key is index option text and value is index number
            if ligand_name in indexfile_inputkey:
                ligandname_index = indexfile_inputvalue
            if "[ Protein ]" == indexfile_inputkey:
                protein_index = indexfile_inputvalue
        maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
        # print indexfile_input_dict[maximum_key_ndx_input]
        receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
        protien_ligand_complex_index = receptor_index + 1
        ligand_name_index = protien_ligand_complex_index + 1
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + command_tool+"/"+md_mutation_folder +"/"+ "gmx_make_ndx_input.txt", "w")
        file_gmx_make_ndx_input.write(
            str(protein_index) + "\nname " + str(receptor_index) + " receptor\n" + str(protein_index) + " | " + str(
                ligandname_index) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n" +str(ligandname_index)+"\nname "+str(ligand_name_index)+" ligand"+"\nq\n")
        file_gmx_make_ndx_input.close()
        gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -n " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+ command_tool + '/' + md_mutation_folder + "/" + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + group_project_name+'/'+project_name +"/" +command_tool + "/" + md_mutation_folder + '/' + \
                       config.PATH_CONFIG[
                           'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                           'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_make_ndx_input.txt"

        print(" make index command")
        print(gmx_make_ndx)
        os.system(gmx_make_ndx)

    perform_cmd_trajconv_designer_queue(project_name, project_id, md_simulations_tpr_file, md_simulations_ndx_file,md_mutation_folder,command_tool)
    # ===================   post processing after make index  ===============================
    # copy MD .tpr file to MMPBSA working directory
    source_tpr_md_file = config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/'+command_tool+"/"+md_mutation_folder+"/" + md_simulations_tpr_file
    tpr_file_split = md_simulations_tpr_file.split("/")
    dest_tpr_md_file = config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
                       config.PATH_CONFIG['mmpbsa_project_path'] + tpr_file_split[1]

    shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

    # copy topology file from MS to MMPBSA working directory
    source_topology_file = config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +  tpr_file_split[0] + "/topol.top"
    dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top"
    shutil.copyfile(source_topology_file, dest_topology_file)

    # copy ligand .itp files
    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
        ligand_name_split = ligand_inputvalue.split("_")
        source_itp_file = config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' +command_tool+"/"+md_mutation_folder+"/"+ tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
        dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path'] + ligand_name_split[0] + ".itp"
        shutil.copyfile(source_itp_file, dest_itp_file)

    # copy atom_types.itp file from MD dir
    source_atomtype_itp_file = config.PATH_CONFIG[
                                   'local_shared_folder_path'] + group_project_name+'/'+project_name + '/' +command_tool +"/"+ md_mutation_folder +"/"+ tpr_file_split[0] + "/" + "atomtypes" + ".itp"
    dest_atomtype_itp_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+ "/" +md_mutation_folder +"/" +config.PATH_CONFIG['mmpbsa_project_path'] + "atomtypes" + ".itp"
    shutil.copyfile(source_atomtype_itp_file, dest_atomtype_itp_file)

    key_name_ligand_input = 'mmpbsa_input_ligand'

    # processing itp files
    pre_process_designer_queue_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input,md_mutation_folder,command_tool)

    # ----------------------   make a "trail" directory for MMPBSA   -----------------------
    os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path'] + "trial")
    # copying MMPBSA input files to trail directory
    # copy .XTC file
    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                    config.PATH_CONFIG['mmpbsa_project_path'] + "merged-recentered.xtc",
                    config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.xtc")

    # copy other input files for MMPBSA
    for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path']):
        # copy .TPR file
        if file_name.endswith(".tpr"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.tpr")
        # copy .NDX file
        if file_name.endswith(".ndx"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/index.ndx")

        # copy .TOP file
        if file_name.endswith(".top"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)
        # copy .ITP files
        if file_name.endswith(".itp"):
            # check for multiple ligand
            if multiple_ligand_input:
                # for multiple ligand
                # renaming user input ligand as LIGAND
                key_name_ligand_input = 'mmpbsa_input_ligand'

                ProjectToolEssentials_res_ligand_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_ligand_input).latest('entry_time')
                ligand_name = ProjectToolEssentials_res_ligand_input.key_values
            else:
                # for single ligand
                for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                    ligand_name = ligand_inputvalue.split("_")[0]

            if file_name[:-4] == ligand_name:
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+\
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/ligand.itp")
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)
            else:
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)

    # ----------------   re-creating topology file   -------------------------
    topology_contents_part1 = ""
    topology_contents_part2 = ""
    topology_contents_part3 = ""
    topology_content_filtered = ""
    topology_file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top"

    # get topology file [ molecules ] section contents
    with open(topology_file_path) as topol_file:
        for line_topol in topol_file:
            topology_contents_part1 += line_topol
            if line_topol.strip() == '[ moleculetype ]':
                break

    # get topology file itp section
    with open(topology_file_path) as topol_file:
        for line in topol_file:
            if line.strip() == '; Include Position restraint file':  # Or whatever test is needed
                break
        # Reads text until the end of the block:
        for line in topol_file:  # This keeps reading the file
            topology_contents_part2 += line  # Line is extracted (or block_of_lines.append(line), etc.)
    topology_content_filtered = '\n'.join(topology_contents_part1.split('\n')[:-2])

    ligand_itp_exists = True  # for more than one ligand
    for line_seg in topology_contents_part2.split("\n"):
        if re.match('^#include\s*\".*\.itp\"', line_seg):
            if any(ligand_inputvalue.split("_")[0] in line_seg for ligand_inputkey, ligand_inputvalue in
                   CatMec_input_dict.iteritems()):
                if ligand_itp_exists == False:
                    pass
                else:
                    topology_contents_part3 += '#include "complex.itp" ' + '\n'
                    topology_contents_part3 += '#include "ligand.itp" ' + '\n'
                    ligand_itp_exists = False
            else:
                topology_contents_part3 += line_seg + '\n'
        else:
            topology_contents_part3 += line_seg + '\n'

    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol_original.top", "w+") as new_topol:
        new_topol.write(topology_content_filtered + topology_contents_part3)
    # renaming topology file
    os.rename(config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top",
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "trial/backup_topology.txt"
              )
    os.rename(config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol_original.top",
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "trial/topol.top"
              )
    # ----------------   END of re-creating topology file   -------------------------

    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
             config.PATH_CONFIG['mmpbsa_project_path'])
    # =========================    execute GMXMMPBSA shell script 0    =================================================
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_one'])
    # change dir if required
    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
             config.PATH_CONFIG['mmpbsa_project_path'])

    # =========================    execute GMXMMPBSA shell script 1    =================================================
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])

    # change dir if required
    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
             config.PATH_CONFIG['mmpbsa_project_path'])

    # =========================    execute GMXMMPBSA shell script 2    =================================================
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])
    return JsonResponse({"success": True})


@csrf_exempt
def generate_hotspot_slurm_script(file_path, server_name, job_name, number_of_threads,GMX_run_file_one,GMX_run_file_two,GMX_run_file_three):
    print('inside generate_hotspot_slurm_script function')
    new_shell_script_lines = ''
    pre_simulation_script_file_name = 'pre_simulation.sh'
    simulation_script_file_name = 'simulation_windows_format.sh'
    print('before opening ',file_path + pre_simulation_script_file_name)
    with open(file_path + pre_simulation_script_file_name,'r') as source_file:
        print('inside opening ', file_path + pre_simulation_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path + simulation_script_file_name):
        print('removing ',file_path + simulation_script_file_name)
        os.remove(file_path + simulation_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path + simulation_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path + simulation_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write("rsync $SLURM_SUBMIT_DIR/* /scratch/$SLURM_JOB_ID\n")
        new_bash_script.write("cd /scratch/$SLURM_JOB_ID\n")
        new_bash_script.write("sh "+GMX_run_file_one+"\n")
        new_bash_script.write("sh "+GMX_run_file_two+"\n")
        new_bash_script.write("sh "+GMX_run_file_three+"\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True


def hotspot_analyse_mmpbsa(request,mutation_dir_mmpbsa, project_name, command_tool,project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    #MMPBSA for hotspot module
    entry_time = datetime.now()
    # get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "hotspot_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    hotspot_mutations_file = ProjectToolEssentials_mutations_file.key_values

    #create MMPBSA dir only
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/")

    # -----------------------------------------------------------------------------------------------------
    # --------------------    get TRJCAT command string to be executed    ---------------------------------
    # -----------------------------------------------------------------------------------------------------

    trajcat_return_list = get_hotspot_trjcat_command_str(request,mutation_dir_mmpbsa,  project_name, command_tool, project_id, user_id)

    print("trajcat_return_list is ====================")
    print(trajcat_return_list)
    print("list  0000000 item is trajcat_return_list[0]")
    print(trajcat_return_list[0])

    print("list  44444 item is trajcat_return_list[4]")
    print(trajcat_return_list[4])
    # return list of values (0 - gro files str, 1 - tpr file str, 2 - index file str, 3 - topology file)
    # [em_gro_file_str, em_tpr_file_str, md_index_file_str,md_topology_file_str]
    # -----------------------------------------------------------------------------------------------------
    # --------------------    TRJCAT RUN   ----------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------

    gmx_trjcat_cmd = "gmx trjcat -f " + trajcat_return_list[4] + " -o " + config.PATH_CONFIG[
       'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" +command_tool + "/" +mutation_dir_mmpbsa+"/MMPBSA/"+ "merged.xtc -keeplast -cat"

    os.system(gmx_trjcat_cmd)

    # -----------------------------------------------------------------------------------------------------
    # --------------------   END TRJCAT RUN   ----------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------
    ndx_count = 0
    ndx_input_dict = {}
    #get index file '[]' data and count in dictionary
    with open(trajcat_return_list[2], 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            if re.match("^\[.*\]\n", line):
                ndx_input_dict.update({line.strip(): ndx_count})
                ndx_count += 1

    md_simulations_tpr_file = trajcat_return_list[1]

    md_simulations_ndx_file = trajcat_return_list[2]

    key_name_CatMec_input = 'substrate_input'
    command_tootl_title = "CatMec"
    # get list of ligand inputs
    ProjectToolEssentials_res_CatMec_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                   key_name=key_name_CatMec_input).latest('entry_time')
    CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.key_values)
    # if User has only one ligand as input
    multiple_ligand_input = False
    if len(CatMec_input_dict) > 1:
        multiple_ligand_input = True

    indexfile_input_dict = ndx_input_dict

    '''
                                                                                      oooo                                                .o8              
                                                                              `888                                               "888              
     .oooooooo ooo. .oo.  .oo.   oooo    ooo      ooo. .oo.  .oo.    .oooo.    888  oooo   .ooooo.              ooo. .oo.    .oooo888  oooo    ooo 
    888' `88b  `888P"Y88bP"Y88b   `88b..8P'       `888P"Y88bP"Y88b  `P  )88b   888 .8P'   d88' `88b             `888P"Y88b  d88' `888   `88b..8P'  
    888   888   888   888   888     Y888'          888   888   888   .oP"888   888888.    888ooo888              888   888  888   888     Y888'    
    `88bod8P'   888   888   888   .o8"'88b         888   888   888  d8(  888   888 `88b.  888    .o              888   888  888   888   .o8"'88b   
    `8oooooo.  o888o o888o o888o o88'   888o      o888o o888o o888o `Y888""8o o888o o888o `Y8bod8P' ooooooooooo o888o o888o `Y8bod88P" o88'   888o 
    d"     YD                                                                                                                                      
    "Y88888P'                                                                                                                                      
    '''
    if multiple_ligand_input:
        # for multiple ligand input
        print("for multiple ligand input")
        # get user input ligand name from DB
        key_name_ligand_input = 'mmpbsa_input_ligand'

        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.key_values
        # extract ligand number
        if "[ " + ligand_name + " ]" in indexfile_input_dict.keys():
            ligand_name_input = str(indexfile_input_dict["[ " + ligand_name + " ]"])
        indexfile_complex_option_input = ""
        indexfile_receptor_option_input = ""
        # prepare receptor option input string
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            dict_ligand_name = ligand_name_split[0]
            if "[ " + dict_ligand_name + " ]" in indexfile_input_dict.keys() and dict_ligand_name != ligand_name:
                indexfile_receptor_option_input += str(indexfile_input_dict["[ " + dict_ligand_name + " ]"]) + " | "
        # prepare complex option input string
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            dict_ligand_name = ligand_name_split[0]
            if "[ " + dict_ligand_name + " ]" in indexfile_input_dict.keys():
                indexfile_complex_option_input += str(indexfile_input_dict["[ " + dict_ligand_name + " ]"]) + " | "

        if "[ Protein ]" in indexfile_input_dict.keys():
            indexfile_complex_option_input += str(indexfile_input_dict["[ Protein ]"])
            indexfile_receptor_option_input += str(indexfile_input_dict["[ Protein ]"])
        # reverse the strings
        indexfile_complex_option_input = indexfile_complex_option_input.split(" | ")
        indexfile_complex_option_input = indexfile_complex_option_input[-1::-1]
        reversed_indexfile_complex_option_input = ' | '.join(indexfile_complex_option_input)

        indexfile_receptor_option_input = indexfile_receptor_option_input.split(" | ")
        indexfile_receptor_option_input = indexfile_receptor_option_input[-1::-1]
        reversed_indexfile_receptor_option_input = ' | '.join(indexfile_receptor_option_input)
        print(reversed_indexfile_complex_option_input)
        print(reversed_indexfile_receptor_option_input)
        maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
        receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
        protien_ligand_complex_index = receptor_index + 1
        # write protien ligand complex index number to DB
        entry_time = datetime.now()
        '''
        key_name_protien_ligand_complex_index = 'mmpbsa_index_file_protien_ligand_complex_number'
        ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(
            tool_title=commandDetails_result.command_tool,
            project_id=project_id,
            key_name=key_name_protien_ligand_complex_index,
            values=protien_ligand_complex_index,
            entry_time=entry_time)
        result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
        '''
        ligand_name_index = protien_ligand_complex_index + 1
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt",
                                       "w")
        file_gmx_make_ndx_input.write(
            str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(
                reversed_indexfile_complex_option_input) + "\nname " + str(
                protien_ligand_complex_index) + " complex" + "\n" + str(ligand_name_input) + "\nname " + str(
                ligand_name_index) + " ligand" + "\nq\n")
        file_gmx_make_ndx_input.close()

        gmx_make_ndx = "gmx make_ndx -f " + md_simulations_tpr_file + " -n " + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+ command_tool + "/" + mutation_dir_mmpbsa + '/MMPBSA/' + "index.ndx < " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt"

        print(" make index command in HOTSPOT MMPBSA")
        print(gmx_make_ndx)
        os.system(gmx_make_ndx)

    else:
        # for single ligand input
        # get ligand name
        ligand_name = ""
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name = ligand_inputvalue.split("_")[0]
        # prepare input file for gmx make_ndx command
        protein_index = 0
        ligandname_index = 0
        for indexfile_inputkey, indexfile_inputvalue in indexfile_input_dict.iteritems():  # key is index option text and value is index number
            if ligand_name in indexfile_inputkey:
                ligandname_index = indexfile_inputvalue
            if "[ Protein ]" == indexfile_inputkey:
                protein_index = indexfile_inputvalue
        maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
        # print indexfile_input_dict[maximum_key_ndx_input]
        receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
        protien_ligand_complex_index = receptor_index + 1
        ligand_name_index = protien_ligand_complex_index + 1
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt",
                                       "w")
        file_gmx_make_ndx_input.write(
            str(protein_index) + "\nname " + str(receptor_index) + " receptor\n" + str(protein_index) + " | " + str(
                ligandname_index) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n" +str(ligandname_index)+"\nname "+str(ligand_name_index)+" ligand"+"\nq\n")
        file_gmx_make_ndx_input.close()
        gmx_make_ndx = "gmx make_ndx -f " + md_simulations_tpr_file + " -n " + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+ command_tool + "/" + mutation_dir_mmpbsa + '/MMPBSA/' + "index.ndx < " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt"

        print(" make index command in HOTSPOT MMPBSA")
        print(gmx_make_ndx)
        os.system(gmx_make_ndx)

    # -------------------------   Call to execute trajconv command -----------------------------------------------------
    perform_cmd_trajconv_hotspot_mmpbsa(project_name, project_id, md_simulations_tpr_file, md_simulations_ndx_file,
                                        mutation_dir_mmpbsa, command_tool)

    # ==================================================================================================================
    # ===================   post processing after make index  ==========================================================
    # ==================================================================================================================

    # ------------------   copy MD .tpr file to MMPBSA working directory   ---------------------------------------------
    source_tpr_md_file = md_simulations_tpr_file
    tpr_file_split = md_simulations_tpr_file.split("/")
    dest_tpr_md_file = config.PATH_CONFIG[
                           'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + tpr_file_split[-1]

    shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

    # ------------------   copy topology file from MS to MMPBSA working directory   ------------------------------------
    source_topology_file = trajcat_return_list[3] # topology file
    dest_topology_file = config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top"
    shutil.copyfile(source_topology_file, dest_topology_file)

    # ------------------   copy ligand .itp files   --------------------------------------------------------------------
    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
        ligand_name_split = ligand_inputvalue.split("_")
        # rsplit is a shorthand for "reverse split", and unlike regular split works from the end of a string.
        source_itp_file = md_simulations_tpr_file.rsplit("/",1)[0] + "/" + ligand_name_split[0] + ".itp"
        dest_itp_file = config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + ligand_name_split[0] + ".itp"
        shutil.copyfile(source_itp_file, dest_itp_file)

    # copy atom_types.itp file from MD dir
    source_atomtype_itp_file = trajcat_return_list[3][:-10] + "/" + "atomtypes" + ".itp"
    dest_atomtype_itp_file = config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "atomtypes" + ".itp"
    shutil.copyfile(source_atomtype_itp_file, dest_atomtype_itp_file)


    key_name_ligand_input = 'mmpbsa_input_ligand'
    # processing itp files
    pre_process_hotspot_mmpbsa_imput(project_id, project_name, md_simulations_tpr_file, CatMec_input_dict,
                                            key_name_ligand_input, mutation_dir_mmpbsa, command_tool)

    # ----------------------   make a "trail" directory for MMPBSA   -----------------------
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial")

    # -----------------   copying MMPBSA input files to trail directory   ----------------------------------------------
    # -----------------   copy .XTC file   -----------------------------------------------------------------------------
    shutil.copyfile(config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged-recentered.xtc",
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/npt.xtc")

    # -----------   copy other input files for MMPBSA   ----------------------------------------------------------------
    for file_name in os.listdir(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" ):
        # -------------   copy .TPR file   -----------------------------------------------------------------------------
        if file_name.endswith(".tpr"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/npt.tpr")
        # -------------   copy .NDX file   -----------------------------------------------------------------------------
        if file_name.endswith(".ndx"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/index.ndx")

        # -------------   copy .TOP file   -----------------------------------------------------------------------------
        if file_name.endswith(".top"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)
        # -------------   copy .ITP files   ----------------------------------------------------------------------------
        if file_name.endswith(".itp"):
            # check for multiple ligand
            if multiple_ligand_input:
                # for multiple ligand
                # renaming user input ligand as LIGAND
                key_name_ligand_input = 'mmpbsa_input_ligand'

                ProjectToolEssentials_res_ligand_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_ligand_input).latest('entry_time')
                ligand_name = ProjectToolEssentials_res_ligand_input.key_values
            else:
                # for single ligand
                for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                    ligand_name = ligand_inputvalue.split("_")[0]

            if file_name[:-4] == ligand_name:
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/ligand.itp")
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)
            else:
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)

    # ----------------   re-creating topology file   -------------------------
    topology_contents_part1 = ""
    topology_contents_part2 = ""
    topology_contents_part3 = ""
    topology_content_filtered = ""
    topology_file_path = config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/topol.top"

    # get topology file [ molecules ] section contents
    with open(topology_file_path) as topol_file:
        for line_topol in topol_file:
            topology_contents_part1 += line_topol
            if line_topol.strip() == '[ moleculetype ]':
                break

    # get topology file itp section
    with open(topology_file_path) as topol_file:
        for line in topol_file:
            if line.strip() == '; Include Position restraint file':  # Or whatever test is needed
                break
        # Reads text until the end of the block:
        for line in topol_file:  # This keeps reading the file
            topology_contents_part2 += line  # Line is extracted (or block_of_lines.append(line), etc.)
    topology_content_filtered = '\n'.join(topology_contents_part1.split('\n')[:-2])

    ligand_itp_exists = True  # for more than one ligand
    for line_seg in topology_contents_part2.split("\n"):
        if re.match('^#include\s*\".*\.itp\"', line_seg):
            if any(ligand_inputvalue.split("_")[0] in line_seg for ligand_inputkey, ligand_inputvalue in
                   CatMec_input_dict.iteritems()):
                if ligand_itp_exists == False:
                    pass
                else:
                    topology_contents_part3 += '#include "complex.itp" ' + '\n'
                    topology_contents_part3 += '#include "ligand.itp" ' + '\n'
                    ligand_itp_exists = False
            else:
                topology_contents_part3 += line_seg + '\n'
        else:
            topology_contents_part3 += line_seg + '\n'

    with open(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/topol_original.top", "w+") as new_topol:
        new_topol.write(topology_content_filtered + topology_contents_part3)
    # renaming topology file
    os.rename(config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/topol.top",
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/backup_topology.txt"
              )
    os.rename(config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/topol_original.top",
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/topol.top"
              )
    # ----------------   END of re-creating topology file   -------------------------

    #changing directory to MMPBSA
    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/")
    # --- get server slected by user ----
    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values
    # -- get the slurm boolean value from DB
    slurm_key = "md_simulation_slurm_selection_value"
    slurm_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                 key_name=slurm_key).latest(
        'entry_time')

    slurm_value = slurm_ProjectToolEssentials_res.key_values
    # =======================  get user input threads  ============================
    key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
    ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_mmpbsa_threads_input).latest('entry_time')
    catmec_mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
    # ======================= End of get user input threads  ======================
    if slurm_value == "yes": # queue to slurm
        initial_string = 'QZW'
        module_name = 'Hotspot_Mutations_mmpbsa'
        job_name = initial_string + '_' + str(project_id) + '_' + module_name
        # generate_slurm_script(dest_file_path, server_value, job_name, number_of_threads)
        # generating slurm batch script
        # =======================  get user input threads  ============================
        key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
        ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_mmpbsa_threads_input).latest('entry_time')
        catmec_mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
        # ======================= End of get user input threads  ======================

        # ======================= Start of get directory to queue or work in  ======================
        md_simulation_file_path = '/CatMec/MD_Simulation/pre_simulation.sh'
        source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + md_simulation_file_path
        destination_file_path = config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/"
        try:
            print("inside try")
            shutil.copy(str(source_file_path) , str(destination_file_path))
        except IOError as e:
            print("Unable to copy file. %s" % e)
            pass
        except Exception:
            print("Unexpected error:", sys.exc_info())
            pass
        # ======================= End of get directory to queue or work in  ======================
        GMX_run_file_one = config.PATH_CONFIG['GMX_run_file_one']
        GMX_run_file_two = config.PATH_CONFIG['GMX_run_file_two']
        GMX_run_file_three = config.PATH_CONFIG['GMX_run_file_three']
        generate_hotspot_slurm_script(destination_file_path, server_value, job_name, catmec_mmpbsa_threads_input,GMX_run_file_one,GMX_run_file_two,GMX_run_file_three)
        # with open(config.PATH_CONFIG[
        #          'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + 'queue_mmpbsa.sh', 'w+') as slurm_bash_script:
        #     slurm_bash_script.write('''\
        #                 #!/bin/bash
        #                 #SBATCH --partition=$1     ### Partition
        #                 #SBATCH --job-name=$2      ### jobname QZW_project-id_module-name_no-of-runs
        #                 #SBATCH --time=100:00:00     ### WallTime
        #                 #SBATCH --nodes=1            ### Number of Nodes
        #                 #SBATCH --ntasks-per-node=$6 ### Number of tasks (MPI processes)
        #
        #                 rsync -avz $SLURM_SUBMIT_DIR/* /scratch/$SLURM_JOB_ID
        #                 cd /scratch/$SLURM_JOB_ID
        #                 sh $3
        #                 sh $4
        #                 sh $5
        #                 rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/
        #                 ''')
        print('after generate_slurm_script ************************************************************************')
        print('before changing directory')
        print(os.getcwd())
        print('after changing directory')
        os.chdir(destination_file_path)
        print(os.getcwd())
        print("Converting from windows to unix format")
        print("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
        os.system("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
        print('queuing **********************************************************************************')
        cmd = "sbatch " + destination_file_path + "simulation.sh"
        print("Submitting Job1 with command: %s" % cmd)
        status, jobnum = commands.getstatusoutput(cmd)
        print("job id is ", jobnum)
        print("status is ", status)
        print("job id is ", jobnum)
        print("status is ", status)
        print(jobnum.split())
        lenght_of_split = len(jobnum.split())
        index_value = lenght_of_split - 1
        print(jobnum.split()[index_value])
        job_id = jobnum.split()[index_value]
        # save job id
        job_id_key_name = "job_id"
        entry_time = datetime.now()
        try:
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_name)
            QzwSlurmJobDetails_save_job_id.save()
        except db.OperationalError as e:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in except of HOTSPOT SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                project_id=project_id,
                                                                entry_time=entry_time,
                                                                job_id=job_id,
                                                                job_status="1",
                                                                job_title=job_name)
            QzwSlurmJobDetails_save_job_id.save()
            print("saved")
        except Exception as e:
            print(
                "<<<<<<<<<<<<<<<<<<<<<<< in except of HOTSPOT SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("exception is ", str(e))
            pass
            '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                   project_id=project_id,
                                                                                   entry_time=entry_time,
                                                                                   values=job_id,
                                                                                   job_id=job_id)
            QzwSlurmJobDetails_save_job_id.save()
            print("saved")'''
        print('queued')

        # print('sbatch '
        #           + config.PATH_CONFIG[
        #               'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + 'queue_mmpbsa.sh '+ str(
        #     server_value) + ' ' + str(job_name) + ' ' + str(config.PATH_CONFIG['GMX_run_file_one']) + ' ' + str(
        #     config.PATH_CONFIG['GMX_run_file_two']) + ' ' + str(config.PATH_CONFIG['GMX_run_file_three'])+ ' '+str(catmec_mmpbsa_threads_input))
        # os.system('sbatch '
        #           + config.PATH_CONFIG[
        #               'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + 'queue_mmpbsa.sh ' + str(
        #     server_value) + ' ' + str(job_name) + ' ' + str(config.PATH_CONFIG['GMX_run_file_one']) + ' ' + str(
        #     config.PATH_CONFIG['GMX_run_file_two']) + ' ' + str(config.PATH_CONFIG['GMX_run_file_three']))
        # print('queued')
    else: # run raw command (without slurm)
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_one'])
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/")
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/")
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])
    return JsonResponse({"success": True})


#trajcat for Hotspot MMPBSA module
def get_hotspot_trjcat_command_str(request,mutation_dir_mmpbsa,  project_name, command_tool, project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    em_gro_file_str = ""
    em_tpr_file_str = ""
    md_index_file_str = ""
    md_topology_file_str = ""
    em_em_xtc_file_str = ""
    variant_index_dir = 0  # variant dirs counter
    for mutations_dirs in os.listdir(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                     +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa):
        # ---------- loop for variant dirs ---------------
        if os.path.isdir(os.path.join(config.PATH_CONFIG[
                                          'local_shared_folder_path_project'] + 'Project/' + group_project_name+'/'+project_name + '/' + command_tool + '/' +mutation_dir_mmpbsa,
                                      mutations_dirs)):
            # ------------ loop for mutations dir -----------------
            pdb_file_index_str = 0  # index for PDB (file) variant
            for variants_dir in os.listdir(config.PATH_CONFIG[
                                               'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa + "/" + mutations_dirs + "/"):
                # <<<<<<<<<<<<<< loop for variants dir >>>>>>>>>>>>>>>>>
                if variants_dir.strip() == "md_run1":
                    for md_run_dir in os.listdir(config.PATH_CONFIG[
                                                       'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/"+mutations_dirs+"/"+variants_dir+"/"):
                        #filter for em.gro file
                        if md_run_dir.strip() == "em.gro":
                            em_gro_file_str += config.PATH_CONFIG[
                                                       'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/"+mutations_dirs+"/"+variants_dir+"/" + md_run_dir.strip() + " "

                        # filter for em.tpr file
                        if md_run_dir.strip() == "em.tpr":
                            em_tpr_file_str = str(config.PATH_CONFIG[
                                                       'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/"+mutations_dirs+"/"+variants_dir+"/" + md_run_dir.strip())

                        # filter for index file
                        if md_run_dir.strip() == "index.ndx":
                            md_index_file_str = str(config.PATH_CONFIG[
                                                       'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/"+mutations_dirs+"/"+variants_dir+"/" + md_run_dir.strip())

                        # filter for topology file
                        if md_run_dir.strip() == "topol.top":
                            md_topology_file_str = str(config.PATH_CONFIG[
                                                        'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/"+mutations_dirs+"/"+variants_dir+"/" + md_run_dir.strip())

                        #em_em
                        # filter for em_em.xtc file
                        if md_run_dir.strip() == "em_em.xtc":
                            em_em_xtc_file_str += str(config.PATH_CONFIG[
                                                           'local_shared_folder_path_project'] + 'Project/' +group_project_name+'/'+ project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa + "/" + mutations_dirs + "/" + variants_dir + "/" + md_run_dir.strip()+" ")

                    pdb_file_index_str += 1
    variant_index_dir += 1
    # return list of values (0 - gro files str, 1 - tpr file str, 2 - index file str)
    print("in get_hotspot_trjcat_command_str function >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(em_gro_file_str)
    return [em_gro_file_str,em_tpr_file_str,md_index_file_str,md_topology_file_str,em_em_xtc_file_str]

def perform_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file):
    group_project_name = get_group_project_name(str(project_id))
    '''
                                                                              .                o8o
                                                                    .o8                `"'
                     .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .ooooo.  ooo. .oo.   oooo    ooo
                    888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 d88' `88b `888P"Y88b   `88.  .8'
                    888   888   888   888   888     Y888'           888    888         888 888       888   888  888   888    `88..8'
                    `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 888   888  888   888     `888'
                    `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y8bod8P' o888o o888o     `8'
                    d"     YD                                                          888
                    "Y88888P'                                                      .o. 88P
                                                                                   `Y888P
                    '''
    # create input file for trjconv command
    file_gmx_trjconv_input = open(config.PATH_CONFIG[
                                      'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                                      'md_simulations_path'] + "gmx_trjconv_input.txt", "w")
    file_gmx_trjconv_input.write("1\n0\nq\n")
    file_gmx_trjconv_input.close()
    time.sleep(3)
    '''gmx_trjconv = "gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
                  config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                      'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + "gmx_trjconv_input.txt"'''

    os.system("gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + "gmx_trjconv_input.txt")

def perform_cmd_trajconv_designer_queue(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file,md_mutation_folder,command_tool):
    group_project_name = get_group_project_name(str(project_id))
    '''
                                                                              .                o8o
                                                                    .o8                `"'
                     .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .ooooo.  ooo. .oo.   oooo    ooo
                    888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 d88' `88b `888P"Y88b   `88.  .8'
                    888   888   888   888   888     Y888'           888    888         888 888       888   888  888   888    `88..8'
                    `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 888   888  888   888     `888'
                    `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y8bod8P' o888o o888o     `8'
                    d"     YD                                                          888
                    "Y88888P'                                                      .o. 88P
                                                                                   `Y888P
                    '''
    # create input file for trjconv command
    file_gmx_trjconv_input = open(config.PATH_CONFIG[
                                      'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' +command_tool+"/" +md_mutation_folder+"/"+"gmx_trjconv_input.txt", "w")
    file_gmx_trjconv_input.write("1\n0\nq\n")
    file_gmx_trjconv_input.close()
    time.sleep(3)
    '''gmx_trjconv = "gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
                  config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                      'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + "gmx_trjconv_input.txt"'''

    os.system("gmx trjconv -f " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+ command_tool + "/" + md_mutation_folder + "/" + config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
              config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_ndx_file + " < " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_trjconv_input.txt")



def perform_cmd_trajconv_hotspot_mmpbsa(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file,mutation_dir_mmpbsa,command_tool):
    group_project_name = get_group_project_name(str(project_id))
    '''
       ____ __  ____  __  _____           _
      / ___|  \/  \ \/ / |_   _| __ __ _ (_) ___ ___  _ ____   __
     | |  _| |\/| |\  /    | || '__/ _` || |/ __/ _ \| '_ \ \ / /
     | |_| | |  | |/  \    | || | | (_| || | (_| (_) | | | \ V /
      \____|_|  |_/_/\_\   |_||_|  \__,_|/ |\___\___/|_| |_|\_/
                                       |__/
    '''
    # create input file for trjconv command
    file_gmx_trjconv_input = open(config.PATH_CONFIG[
                                      'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' +command_tool+"/" +mutation_dir_mmpbsa+"/"+"gmx_trjconv_input.txt", "w")
    file_gmx_trjconv_input.write("1\n0\nq\n")
    file_gmx_trjconv_input.close()
    time.sleep(3)
    '''gmx_trjconv = "gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
                  config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                      'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + "gmx_trjconv_input.txt"'''

    os.system("gmx trjconv -f " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+ command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged.xtc -s " + md_simulations_tpr_file + " -pbc mol -ur compact -o " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged-recentered.xtc -center -n " + md_simulations_ndx_file + " < " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_trjconv_input.txt")


def pre_process_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input):
    group_project_name = get_group_project_name(str(project_id))
    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.key_values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/topol.top") as topol_file:
        for line in topol_file:
            if line.strip() == '[ atoms ]':  # start from atoms section
                break
        for line in topol_file:  # End at bonds sections
            if line.strip() == '[ bonds ]':
                break
            count_line += 1
            if line not in ['\n', '\r\n']: # remove new lines and empty lines
                line_list.append(line)  # line[:-1]
    atoms_final_count = line_list[-1].split()[0]
    dihedrals_count = 0
    #==================== End of get ATOMS final count  ===========================
    #check length of ligands inputs from ligand_parameterization
    if len(CatMec_input_dict) > 1:
        #multiple ligands
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            if ligand_inputvalue.split("_")[0] != ligand_name:  # Filter with user input ligand
                initial_text_content = ""
                topology_file_atoms_content = ""
                topology_file_bonds_content = ""
                topology_file_pairs_content = ""
                topology_file_angles_content = ""
                topology_file_dihedrals_content = ""
                topology_content_atoms = ""
                topology_content_bonds = ""
                topology_content_pairs = ""
                topology_content_angles = ""
                topology_content_dihedrals = ""
                topology_content_dihedrals2 = ""
                topology_initial_content = ""
                dihedrals_list = []

                atoms_lastcount = atoms_final_count
                # initial_text_content = initial_text_content+itp_file_inp[:-4]
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[
                              0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ atoms ]':
                            initial_text_content += line2
                            break
                        initial_text_content += line2
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                atoms_lastcount = int(line2.split()[0]) + int(atoms_final_count)
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_atoms_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_atoms_content += line2
                        except IndexError:
                            pass

                # append edited data fo bonds section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[
                              0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_bonds_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_bonds_content += line2
                        except IndexError:
                            pass

                # append edited data for pairs section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[
                              0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_pairs_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_pairs_content += line2
                        except IndexError:
                            pass

                            # append edited data for angles section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[
                              0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_angles_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_angles_content += line2
                        except IndexError:
                            pass

                            # apend edited data for dihedrals section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[
                              0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            initial_text_content += "\n" + line2
                            break

                    for line2 in itp_file:
                        if line2.strip() == '\n':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[3] + " ",
                                                      str(int(line2.split()[3]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_dihedrals_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_dihedrals_content += line2
                        except IndexError:
                            pass

                # ================================================================================================
                # ====================================== TOPOLOGY FILE ===========================================
                # ================================================================================================
                # write respective contents to topology file
                with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ atoms ]':
                            topology_content_atoms += line2
                            break
                        if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                            topology_initial_content += ";" + line2
                        else:
                            topology_initial_content += line2
                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_atoms += "    " + line2
                            else:
                                topology_content_atoms += line2
                        except IndexError:
                            pass

                # ===================  bonds content  ===========================
                with open(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ bonds ]':
                            topology_content_bonds += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_bonds += "    " + line2
                            else:
                                topology_content_bonds += line2
                        except IndexError:
                            pass

                # ==================   pairs content  ===============================
                with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ pairs ]':
                            topology_content_pairs += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_pairs += "    " + line2
                            else:
                                topology_content_pairs += line2
                        except IndexError:
                            pass

                # =======================   angles content   ==============================
                with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ angles ]':
                            topology_content_angles += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_angles += "    " + line2
                            else:
                                topology_content_angles += line2
                        except IndexError:
                            pass

                # ======================   dihedrals content   ========================
                # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
                # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
                #     for line2 in topology_bak_file:
                #         if line2.strip() == '[ dihedrals ]':
                #             topology_content_dihedrals += line2
                #             break
                #
                #     for line2 in topology_bak_file:
                #         if line2.strip() == "\n":
                #             break
                #         try:
                #             if (line2.split()[0] != ";"):
                #                 topology_content_dihedrals += "    " + line2
                #             else:
                #                 topology_content_dihedrals += line2
                #         except IndexError:
                #             pass
                # ======================   dihedrals content for multiple   ========================
                with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ dihedrals ]':
                            dihedrals_count += 1
                if dihedrals_count > 1:
                    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:

                        # ---------------- commented on 02-08-2019 to fix multiple dihedrals bug
                        # for line2 in topology_bak_file:
                        #     if line2.strip() == '[ dihedrals ]':
                        #         topology_content_dihedrals += line2
                        #         break
                        # for line2 in topology_bak_file:
                        #     if line2.strip() == "\n":
                        #         break
                        #     try:
                        #         if (line2.split()[0].isdigit()):
                        #             topology_content_dihedrals += "    " + line2
                        #     except IndexError:
                        #         pass
                        for line2 in topology_bak_file:
                            if line2.strip() == '[ dihedrals ]':
                                topology_content_dihedrals += line2
                                dihedrals_list.append(line2.replace(" ", ""))
                                break

                        for line2 in topology_bak_file:
                            if re.search(r"\[(\s\w+\s)\]", line2):
                                break
                            try:
                                if (line2.split()[0] != ";"):
                                    topology_content_dihedrals += "    " + line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                                else:
                                    topology_content_dihedrals += line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                            except IndexError:
                                pass

                    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass

                else:
                    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass

                topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
                print("adding topology file contents are")
                # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
                with open(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+'/'+project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "complex.itp", "w") as new_topology_file:
                    new_topology_file.write(topology_initial_content + "\n" +
                                            topology_content_atoms + topology_file_atoms_content + "\n" +
                                            topology_content_bonds + topology_file_bonds_content + "\n" +
                                            topology_content_pairs + topology_file_pairs_content + "\n" +
                                            topology_content_angles + topology_file_angles_content + "\n" +
                                            topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

                atoms_final_count = atoms_lastcount
                with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                          config.PATH_CONFIG['mmpbsa_project_path'] + "new_" + ligand_inputvalue.split("_")[0] + ".itp",
                          "w") as new_itp_file:
                    new_itp_file.write(initial_text_content)
    else:
        #single ligand
        initial_text_content = ""
        topology_file_atoms_content = ""
        topology_file_bonds_content = ""
        topology_file_pairs_content = ""
        topology_file_angles_content = ""
        topology_file_dihedrals_content = ""
        topology_content_atoms = ""
        topology_content_bonds = ""
        topology_content_pairs = ""
        topology_content_angles = ""
        topology_content_dihedrals = ""
        topology_content_dihedrals2 = ""
        topology_initial_content = ""
        dihedrals_list = []

        atoms_lastcount = atoms_final_count

        ''' append edited data fo bonds section


        append edited data for pairs section


        append edited data for angles section


        apend edited data for dihedrals section
        '''

        # ================================================================================================
        # ====================================== TOPOLOGY FILE ===========================================
        # ================================================================================================
        # write respective contents to topology file
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ atoms ]':
                    topology_content_atoms += line2
                    break
                if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                    topology_initial_content += ";" + line2
                else:
                    topology_initial_content += line2
            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_atoms += "    " + line2
                    else:
                        topology_content_atoms += line2
                except IndexError:
                    pass

        # ===================  bonds content  ===========================
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ bonds ]':
                    topology_content_bonds += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_bonds += "    " + line2
                    else:
                        topology_content_bonds += line2
                except IndexError:
                    pass

        # ==================   pairs content  ===============================
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ pairs ]':
                    topology_content_pairs += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_pairs += "    " + line2
                    else:
                        topology_content_pairs += line2
                except IndexError:
                    pass

        # =======================   angles content   ==============================
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ angles ]':
                    topology_content_angles += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_angles += "    " + line2
                    else:
                        topology_content_angles += line2
                except IndexError:
                    pass

        # ======================   dihedrals content   ========================
        # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
        # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
        #     for line2 in topology_bak_file:
        #         if line2.strip() == '[ dihedrals ]':
        #             topology_content_dihedrals += line2
        #             break
        #
        #     for line2 in topology_bak_file:
        #         if line2.strip() == "\n":
        #             break
        #         try:
        #             if (line2.split()[0] != ";"):
        #                 topology_content_dihedrals += "    " + line2
        #             else:
        #                 topology_content_dihedrals += line2
        #         except IndexError:
        #             pass
        # ======================   dihedrals content for multiple   ========================
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ dihedrals ]':
                    dihedrals_count += 1
        if dihedrals_count > 1:
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:

                # ---------------- commented on 02-08-2019 to fix multiple dihedrals bug
                # for line2 in topology_bak_file:
                #     if line2.strip() == '[ dihedrals ]':
                #         topology_content_dihedrals += line2
                #         break
                # for line2 in topology_bak_file:
                #     if line2.strip() == "\n":
                #         break
                #     try:
                #         if (line2.split()[0].isdigit()):
                #             topology_content_dihedrals += "    " + line2
                #     except IndexError:
                #         pass
                for line2 in topology_bak_file:
                    if line2.strip() == '[ dihedrals ]':
                        topology_content_dihedrals += line2
                        dihedrals_list.append(line2.replace(" ", ""))
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_dihedrals += "    " + line2
                            dihedrals_list.append(line2.replace(" ", ""))
                        else:
                            topology_content_dihedrals += line2
                            dihedrals_list.append(line2.replace(" ", ""))
                    except IndexError:
                        pass

            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass

        else:
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass

        topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
        print("adding topology file contents are")
        # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
        with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "complex.itp", "w") as new_topology_file:
            new_topology_file.write(topology_initial_content + "\n" +
                                    topology_content_atoms + topology_file_atoms_content + "\n" +
                                    topology_content_bonds + topology_file_bonds_content + "\n" +
                                    topology_content_pairs + topology_file_pairs_content + "\n" +
                                    topology_content_angles + topology_file_angles_content + "\n" +
                                    topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

        atoms_final_count = atoms_lastcount



    #--------------------   update INPUT.dat file ---------------------------------

    # =======================  get user input temperature  ============================
    key_name_temperature = "preliminary_temp_value"
    ProjectToolEssentials_res_temperature_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_temperature).latest('entry_time')
    temperature_input = ProjectToolEssentials_res_temperature_input.key_values
    # ======================= End of get user input temperature  ======================


    # =======================  get user input threads  ============================
    key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
    ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_mmpbsa_threads_input).latest('entry_time')
    catmec_mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
    # ======================= End of get user input threads  ======================

    new_input_lines = ""
    itp_ligand = "ligand.itp"
    itp_receptor = "complex.itp"
    with open(config.PATH_CONFIG['shared_scripts'] + 'CatMec/Analysis/MMPBSA/'+"INPUT.dat") as mmpbsa_input_file:
        for line in mmpbsa_input_file:
            if ("\titp_ligand" in line):
                line = "\titp_ligand  " + itp_ligand + "\n"
                new_input_lines += line
            elif ("\titp_receptor" in line):
                line = "\titp_receptor  " + itp_receptor + "\n"
                new_input_lines += line
            elif ("temp" in line):
                line = "temp\t\t\t\t\t" + temperature_input + "\n"
                new_input_lines += line
            elif ("mnp" in line):
                line = "mnp\t\t\t\t\t" + catmec_mmpbsa_threads_input + "\n"
                new_input_lines += line
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+'/'+ project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)

#designer queue
def pre_process_designer_queue_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input,md_mutation_folder,command_tool):
    group_project_name = get_group_project_name(str(project_id))
    #=======================  get user input ligand  ============================

    try:
        print("in pre_process_designer_queue_mmpbsa_imput except first DB operation")
        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.key_values
    except db.OperationalError as e:
        print("in pre_process_designer_queue_mmpbsa_imput except first DB operation")
        db.close_old_connections()
        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.key_values

    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/'+command_tool+"/" +md_mutation_folder+"/"+tpr_file_split[0]+"/topol.top") as topol_file:
        for line in topol_file:
            if line.strip() == '[ atoms ]':  # start from atoms section
                break
        for line in topol_file:  # End at bonds sections
            if line.strip() == '[ bonds ]':
                break
            count_line += 1
            if line not in ['\n', '\r\n']: # remove new lines and empty lines
                line_list.append(line)  # line[:-1]
    atoms_final_count = line_list[-1].split()[0]
    dihedrals_count =0
    #==================== End of get ATOMS final count  ===========================
    if len(CatMec_input_dict) > 1:
        # =====================  for multiple ligands   ===========================
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            if ligand_inputvalue.split("_")[0] != ligand_name:  # Filter with user input ligand
                initial_text_content = ""
                topology_file_atoms_content = ""
                topology_file_bonds_content = ""
                topology_file_pairs_content = ""
                topology_file_angles_content = ""
                topology_file_dihedrals_content = ""
                topology_content_atoms = ""
                topology_content_bonds = ""
                topology_content_pairs = ""
                topology_content_angles = ""
                topology_content_dihedrals = ""
                topology_content_dihedrals2 = ""
                topology_initial_content = ""
                dihedrals_list = []

                atoms_lastcount = atoms_final_count
                # initial_text_content = initial_text_content+itp_file_inp[:-4]
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" +
                          tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ atoms ]':
                            initial_text_content += line2
                            break
                        initial_text_content += line2
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                atoms_lastcount = int(line2.split()[0]) + int(atoms_final_count)
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_atoms_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_atoms_content += line2
                        except IndexError:
                            pass

                # append edited data fo bonds section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" +
                          tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_bonds_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_bonds_content += line2
                        except IndexError:
                            pass

                # append edited data for pairs section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" +
                          tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_pairs_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_pairs_content += line2
                        except IndexError:
                            pass

                # append edited data for angles section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" +
                          tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_angles_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_angles_content += line2
                        except IndexError:
                            pass

                # apend edited data for dihedrals section
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/" +
                          tpr_file_split[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp", "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            initial_text_content += "\n" + line2
                            break

                    for line2 in itp_file:
                        if line2.strip() == '\n':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[3] + " ",
                                                      str(int(line2.split()[3]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_dihedrals_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_dihedrals_content += line2
                        except IndexError:
                            pass

                # ================================================================================================
                # ====================================== TOPOLOGY FILE ===========================================
                # ================================================================================================
                # write respective contents to topology file
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ atoms ]':
                            topology_content_atoms += line2
                            break
                        if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                            topology_initial_content += ";" + line2
                        else:
                            topology_initial_content += line2
                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_atoms += "    " + line2
                            else:
                                topology_content_atoms += line2
                        except IndexError:
                            pass

                # ===================  bonds content  ===========================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ bonds ]':
                            topology_content_bonds += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_bonds += "    " + line2
                            else:
                                topology_content_bonds += line2
                        except IndexError:
                            pass

                # ==================   pairs content  ===============================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ pairs ]':
                            topology_content_pairs += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_pairs += "    " + line2
                            else:
                                topology_content_pairs += line2
                        except IndexError:
                            pass

                # =======================   angles content   ==============================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ angles ]':
                            topology_content_angles += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_angles += "    " + line2
                            else:
                                topology_content_angles += line2
                        except IndexError:
                            pass

                # ======================   dihedrals content   ========================
                # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
                # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
                #     for line2 in topology_bak_file:
                #         if line2.strip() == '[ dihedrals ]':
                #             topology_content_dihedrals += line2
                #             break
                #
                #     for line2 in topology_bak_file:
                #         if line2.strip() == "\n":
                #             break
                #         try:
                #             if (line2.split()[0] != ";"):
                #                 topology_content_dihedrals += "    " + line2
                #             else:
                #                 topology_content_dihedrals += line2
                #         except IndexError:
                #             pass
                # ======================   dihedrals content for multiple   ========================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ dihedrals ]':
                            dihedrals_count += 1
                if dihedrals_count > 1:
                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                        for line2 in topology_bak_file:
                            if line2.strip() == '[ dihedrals ]':
                                topology_content_dihedrals += line2
                                dihedrals_list.append(line2.replace(" ", ""))
                                break

                        for line2 in topology_bak_file:
                            if re.search(r"\[(\s\w+\s)\]", line2):
                                break
                            try:
                                if (line2.split()[0] != ";"):
                                    topology_content_dihedrals += "    " + line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                                else:
                                    topology_content_dihedrals += line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                            except IndexError:
                                pass

                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass

                else:
                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+'/'+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                              config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass

                topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
                # print "adding topology file contents are"
                # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "complex.itp", "w") as new_topology_file:
                    new_topology_file.write(topology_initial_content + "\n" +
                                            topology_content_atoms + topology_file_atoms_content + "\n" +
                                            topology_content_bonds + topology_file_bonds_content + "\n" +
                                            topology_content_pairs + topology_file_pairs_content + "\n" +
                                            topology_content_angles + topology_file_angles_content + "\n" +
                                            topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

                atoms_final_count = atoms_lastcount
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                          config.PATH_CONFIG['mmpbsa_project_path'] + "new_" + ligand_inputvalue.split("_")[0] + ".itp",
                          "w") as new_itp_file:
                    new_itp_file.write(initial_text_content)
    else:
        # =====================  for single ligand   ==============================
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            CatMec_input_dict_ligand_name = ligand_inputvalue.split("_")[0]
        initial_text_content = ""
        topology_file_atoms_content = ""
        topology_file_bonds_content = ""
        topology_file_pairs_content = ""
        topology_file_angles_content = ""
        topology_file_dihedrals_content = ""
        topology_content_atoms = ""
        topology_content_bonds = ""
        topology_content_pairs = ""
        topology_content_angles = ""
        topology_content_dihedrals = ""
        topology_content_dihedrals2 = ""
        topology_initial_content = ""
        dihedrals_list = []

        atoms_lastcount = atoms_final_count
        # initial_text_content = initial_text_content+itp_file_inp[:-4]

        # append edited data fo bonds section

        # append edited data for pairs section

        # append edited data for angles section

        # apend edited data for dihedrals section

        # ================================================================================================
        # ====================================== TOPOLOGY FILE ===========================================
        # ================================================================================================
        # write respective contents to topology file
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ atoms ]':
                    topology_content_atoms += line2
                    break
                if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                    topology_initial_content += ";" + line2
                else:
                    topology_initial_content += line2
            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_atoms += "    " + line2
                    else:
                        topology_content_atoms += line2
                except IndexError:
                    pass

        # ===================  bonds content  ===========================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ bonds ]':
                    topology_content_bonds += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_bonds += "    " + line2
                    else:
                        topology_content_bonds += line2
                except IndexError:
                    pass

        # ==================   pairs content  ===============================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ pairs ]':
                    topology_content_pairs += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_pairs += "    " + line2
                    else:
                        topology_content_pairs += line2
                except IndexError:
                    pass

        # =======================   angles content   ==============================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ angles ]':
                    topology_content_angles += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_angles += "    " + line2
                    else:
                        topology_content_angles += line2
                except IndexError:
                    pass

        # ======================   dihedrals content   ========================
        # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
        # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
        #     for line2 in topology_bak_file:
        #         if line2.strip() == '[ dihedrals ]':
        #             topology_content_dihedrals += line2
        #             break
        #
        #     for line2 in topology_bak_file:
        #         if line2.strip() == "\n":
        #             break
        #         try:
        #             if (line2.split()[0] != ";"):
        #                 topology_content_dihedrals += "    " + line2
        #             else:
        #                 topology_content_dihedrals += line2
        #         except IndexError:
        #             pass
        # ======================   dihedrals content for multiple   ========================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ dihedrals ]':
                    dihedrals_count += 1
        if dihedrals_count > 1:
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ dihedrals ]':
                        topology_content_dihedrals += line2
                        dihedrals_list.append(line2.replace(" ", ""))
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_dihedrals += "    " + line2
                            dihedrals_list.append(line2.replace(" ", ""))
                        else:
                            topology_content_dihedrals += line2
                            dihedrals_list.append(line2.replace(" ", ""))
                    except IndexError:
                        pass

            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass

        else:
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                      config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top", "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass

        topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
        # print "adding topology file contents are"
        # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "complex.itp", "w") as new_topology_file:
            new_topology_file.write(topology_initial_content + "\n" +
                                    topology_content_atoms + topology_file_atoms_content + "\n" +
                                    topology_content_bonds + topology_file_bonds_content + "\n" +
                                    topology_content_pairs + topology_file_pairs_content + "\n" +
                                    topology_content_angles + topology_file_angles_content + "\n" +
                                    topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

        atoms_final_count = atoms_lastcount
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
                  config.PATH_CONFIG['mmpbsa_project_path'] + "new_" + CatMec_input_dict_ligand_name + ".itp",
                  "w") as new_itp_file:
            new_itp_file.write(initial_text_content)


    # --------------------   update INPUT.dat file ---------------------------------

    # =======================  get user input temperature  ============================
    key_name_temperature = "preliminary_temp_value"
    ProjectToolEssentials_res_temperature_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_temperature).latest('entry_time')
    temperature_input = ProjectToolEssentials_res_temperature_input.key_values
    # ======================= End of get user input temperature  ======================

    # =======================  get user input threads  ============================
    key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
    ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_mmpbsa_threads_input).latest('entry_time')
    catmec_mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
    # ======================= End of get user input threads  ======================

    new_input_lines = ""
    itp_ligand = "ligand.itp"
    itp_receptor = "complex.itp"
    with open(config.PATH_CONFIG['shared_scripts'] + "CatMec/Analysis/MMPBSA/"+"INPUT.dat") as mmpbsa_input_file:
        for line in mmpbsa_input_file:
            if ("\titp_ligand" in line):
                line = "\titp_ligand  " + itp_ligand + "\n"
                new_input_lines += line
            elif ("\titp_receptor" in line):
                line = "\titp_receptor  " + itp_receptor + "\n"
                new_input_lines += line
            elif ("temp" in line):
                line = "temp\t\t\t\t\t" + temperature_input + "\n"
                new_input_lines += line
            elif ("mnp" in line):
                line = "mnp\t\t\t\t\t" + catmec_mmpbsa_threads_input + "\n"
                new_input_lines += line
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)


#process hotspot mmpbsa inputs
def pre_process_hotspot_mmpbsa_imput(project_id, project_name, md_simulations_tpr_file, CatMec_input_dict,
                                            key_name_ligand_input, mutation_dir_mmpbsa, command_tool):
    group_project_name = get_group_project_name(str(project_id))

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.key_values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/topol.top") as topol_file:
        for line in topol_file:
            if line.strip() == '[ atoms ]':  # start from atoms section
                break
        for line in topol_file:  # End at bonds sections
            if line.strip() == '[ bonds ]':
                break
            count_line += 1
            if line not in ['\n', '\r\n']: # remove new lines and empty lines
                line_list.append(line)  # line[:-1]
    atoms_final_count = line_list[-1].split()[0]
    dihedrals_count = 0
    #==================== End of get ATOMS final count  ===========================
    if len(CatMec_input_dict) > 1:
        #for multiple ligands
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            if ligand_inputvalue.split("_")[0] != ligand_name:  # Filter with user input ligand
                initial_text_content = ""
                topology_file_atoms_content = ""
                topology_file_bonds_content = ""
                topology_file_pairs_content = ""
                topology_file_angles_content = ""
                topology_file_dihedrals_content = ""
                topology_content_atoms = ""
                topology_content_bonds = ""
                topology_content_pairs = ""
                topology_content_angles = ""
                topology_content_dihedrals = ""
                topology_content_dihedrals2 = ""
                topology_initial_content = ""
                dihedrals_list = []

                atoms_lastcount = atoms_final_count
                # initial_text_content = initial_text_content+itp_file_inp[:-4]
                with open(md_simulations_tpr_file.rsplit("/", 1)[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp",
                          "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ atoms ]':
                            initial_text_content += line2
                            break
                        initial_text_content += line2
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                atoms_lastcount = int(line2.split()[0]) + int(atoms_final_count)
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_atoms_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_atoms_content += line2
                        except IndexError:
                            pass

                # append edited data fo bonds section
                with open(md_simulations_tpr_file.rsplit("/", 1)[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp",
                          "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ bonds ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_bonds_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_bonds_content += line2
                        except IndexError:
                            pass

                # append edited data for pairs section
                with open(md_simulations_tpr_file.rsplit("/", 1)[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp",
                          "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ pairs ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_pairs_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_pairs_content += line2
                        except IndexError:
                            pass

                # append edited data for angles section
                with open(md_simulations_tpr_file.rsplit("/", 1)[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp",
                          "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ angles ]':
                            initial_text_content += "\n" + line2
                            break
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_angles_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_angles_content += line2
                        except IndexError:
                            pass

                # apend edited data for dihedrals section
                with open(md_simulations_tpr_file.rsplit("/", 1)[0] + "/" + ligand_inputvalue.split("_")[0] + ".itp",
                          "r+") as itp_file:
                    for line2 in itp_file:
                        if line2.strip() == '[ dihedrals ]':
                            initial_text_content += "\n" + line2
                            break

                    for line2 in itp_file:
                        if line2.strip() == '\n':
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                # pat = re.compile("^\S(.*\S)?$")
                                line2 = line2.replace(line2.split()[0],
                                                      str(int(line2.split()[0]) + int(atoms_final_count)),
                                                      1)
                                line2 = line2.replace(" " + line2.split()[1] + " ",
                                                      str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[2] + " ",
                                                      str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                                line2 = line2.replace(" " + line2.split()[3] + " ",
                                                      str(int(line2.split()[3]) + int(atoms_final_count)), 1)
                                line2 = line2.lstrip()
                                initial_text_content += "    " + line2
                                topology_file_dihedrals_content += "    " + line2
                            else:
                                initial_text_content += line2
                                topology_file_dihedrals_content += line2
                        except IndexError:
                            pass

                # ================================================================================================
                # ====================================== TOPOLOGY FILE ===========================================
                # ================================================================================================
                # write respective contents to topology file
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                          "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ atoms ]':
                            topology_content_atoms += line2
                            break
                        if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                            topology_initial_content += ";" + line2
                        else:
                            topology_initial_content += line2
                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_atoms += "    " + line2
                            else:
                                topology_content_atoms += line2
                        except IndexError:
                            pass

                # ===================  bonds content  ===========================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                          "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ bonds ]':
                            topology_content_bonds += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_bonds += "    " + line2
                            else:
                                topology_content_bonds += line2
                        except IndexError:
                            pass

                # ==================   pairs content  ===============================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                          "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ pairs ]':
                            topology_content_pairs += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_pairs += "    " + line2
                            else:
                                topology_content_pairs += line2
                        except IndexError:
                            pass

                # =======================   angles content   ==============================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                          "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ angles ]':
                            topology_content_angles += line2
                            break

                    for line2 in topology_bak_file:
                        if re.search(r"\[(\s\w+\s)\]", line2):
                            break
                        try:
                            if (line2.split()[0] != ";"):
                                topology_content_angles += "    " + line2
                            else:
                                topology_content_angles += line2
                        except IndexError:
                            pass

                # ======================   dihedrals content   ========================
                # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
                # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
                #     for line2 in topology_bak_file:
                #         if line2.strip() == '[ dihedrals ]':
                #             topology_content_dihedrals += line2
                #             break
                #
                #     for line2 in topology_bak_file:
                #         if line2.strip() == "\n":
                #             break
                #         try:
                #             if (line2.split()[0] != ";"):
                #                 topology_content_dihedrals += "    " + line2
                #             else:
                #                 topology_content_dihedrals += line2
                #         except IndexError:
                #             pass
                # ======================   dihedrals content for multiple   ========================
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                          "r+") as topology_bak_file:
                    for line2 in topology_bak_file:
                        if line2.strip() == '[ dihedrals ]':
                            dihedrals_count += 1
                if dihedrals_count > 1:
                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                              "r+") as topology_bak_file:
                        # for line2 in topology_bak_file:
                        #     if line2.strip() == '[ dihedrals ]':
                        #         topology_content_dihedrals += line2
                        #         break
                        # for line2 in topology_bak_file:
                        #     if line2.strip() == "\n":
                        #         break
                        #     try:
                        #         if (line2.split()[0].isdigit()):
                        #             topology_content_dihedrals += "    " + line2
                        #     except IndexError:
                        #         pass
                        for line2 in topology_bak_file:
                            if line2.strip() == '[ dihedrals ]':
                                topology_content_dihedrals += line2
                                dihedrals_list.append(line2.replace(" ", ""))
                                break

                        for line2 in topology_bak_file:
                            if re.search(r"\[(\s\w+\s)\]", line2):
                                break
                            try:
                                if (line2.split()[0] != ";"):
                                    topology_content_dihedrals += "    " + line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                                else:
                                    topology_content_dihedrals += line2
                                    dihedrals_list.append(line2.replace(" ", ""))
                            except IndexError:
                                pass

                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                              "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass


                else:
                    with open(config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                              "r+") as topology_bak_file:
                        # =================    for second '[ dihedral ]' section    ===================================
                        for line22 in topology_bak_file:
                            if line22.strip() == '[ dihedrals ]':
                                if line22.replace(" ", "") in dihedrals_list:
                                    topology_content_dihedrals2 += line22
                                    break

                        for line22 in topology_bak_file:
                            if line22.strip() in ['\n', '\r\n']:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    break
                            try:
                                if line22.replace(" ", "") not in dihedrals_list:
                                    if (line22.split()[0].isdigit()):
                                        topology_content_dihedrals2 += "    " + line22

                                else:
                                    if line22.replace(" ", "") not in dihedrals_list:
                                        if (line22.split()[0].isdigit()):
                                            topology_content_dihedrals2 += line22

                            except IndexError:
                                pass
                topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
                # print "adding topology file contents are"
                # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "complex.itp",
                          "w") as new_topology_file:
                    new_topology_file.write(topology_initial_content + "\n" +
                                            topology_content_atoms + topology_file_atoms_content + "\n" +
                                            topology_content_bonds + topology_file_bonds_content + "\n" +
                                            topology_content_pairs + topology_file_pairs_content + "\n" +
                                            topology_content_angles + topology_file_angles_content + "\n" +
                                            topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

                atoms_final_count = atoms_lastcount
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "new_" +
                          ligand_inputvalue.split("_")[0] + ".itp", "w") as new_itp_file:
                    new_itp_file.write(initial_text_content)
    else:
        #=========================   for single ligand   ==================================
        initial_text_content = ""
        topology_file_atoms_content = ""
        topology_file_bonds_content = ""
        topology_file_pairs_content = ""
        topology_file_angles_content = ""
        topology_file_dihedrals_content = ""
        topology_content_atoms = ""
        topology_content_bonds = ""
        topology_content_pairs = ""
        topology_content_angles = ""
        topology_content_dihedrals = ""
        topology_content_dihedrals2 = ""
        topology_initial_content = ""
        dihedrals_list = []

        atoms_lastcount = atoms_final_count
        # initial_text_content = initial_text_content+itp_file_inp[:-4]

        # append edited data fo bonds section

        # append edited data for pairs section

        # append edited data for angles section

        # apend edited data for dihedrals section

        # ================================================================================================
        # ====================================== TOPOLOGY FILE ===========================================
        # ================================================================================================
        # write respective contents to topology file
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                  "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ atoms ]':
                    topology_content_atoms += line2
                    break
                if re.match('^#include\s*', line2):  # commenting forcefield and atomtypes lines
                    topology_initial_content += ";" + line2
                else:
                    topology_initial_content += line2
            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_atoms += "    " + line2
                    else:
                        topology_content_atoms += line2
                except IndexError:
                    pass

        # ===================  bonds content  ===========================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                  "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ bonds ]':
                    topology_content_bonds += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_bonds += "    " + line2
                    else:
                        topology_content_bonds += line2
                except IndexError:
                    pass

        # ==================   pairs content  ===============================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                  "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ pairs ]':
                    topology_content_pairs += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_pairs += "    " + line2
                    else:
                        topology_content_pairs += line2
                except IndexError:
                    pass

        # =======================   angles content   ==============================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                  "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ angles ]':
                    topology_content_angles += line2
                    break

            for line2 in topology_bak_file:
                if re.search(r"\[(\s\w+\s)\]", line2):
                    break
                try:
                    if (line2.split()[0] != ";"):
                        topology_content_angles += "    " + line2
                    else:
                        topology_content_angles += line2
                except IndexError:
                    pass

        # ======================   dihedrals content   ========================
        # --- commented on 23-07-2019 to implement new code dihedrals multiple sections
        # with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
        #     for line2 in topology_bak_file:
        #         if line2.strip() == '[ dihedrals ]':
        #             topology_content_dihedrals += line2
        #             break
        #
        #     for line2 in topology_bak_file:
        #         if line2.strip() == "\n":
        #             break
        #         try:
        #             if (line2.split()[0] != ";"):
        #                 topology_content_dihedrals += "    " + line2
        #             else:
        #                 topology_content_dihedrals += line2
        #         except IndexError:
        #             pass
        # ======================   dihedrals content for multiple   ========================
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                  "r+") as topology_bak_file:
            for line2 in topology_bak_file:
                if line2.strip() == '[ dihedrals ]':
                    dihedrals_count += 1
        if dihedrals_count > 1:
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                      "r+") as topology_bak_file:
                # for line2 in topology_bak_file:
                #     if line2.strip() == '[ dihedrals ]':
                #         topology_content_dihedrals += line2
                #         break
                # for line2 in topology_bak_file:
                #     if line2.strip() == "\n":
                #         break
                #     try:
                #         if (line2.split()[0].isdigit()):
                #             topology_content_dihedrals += "    " + line2
                #     except IndexError:
                #         pass
                for line2 in topology_bak_file:
                    if line2.strip() == '[ dihedrals ]':
                        topology_content_dihedrals += line2
                        dihedrals_list.append(line2.replace(" ", ""))
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_dihedrals += "    " + line2
                            dihedrals_list.append(line2.replace(" ", ""))
                        else:
                            topology_content_dihedrals += line2
                            dihedrals_list.append(line2.replace(" ", ""))
                    except IndexError:
                        pass

            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                      "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass


        else:
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top",
                      "r+") as topology_bak_file:
                # =================    for second '[ dihedral ]' section    ===================================
                for line22 in topology_bak_file:
                    if line22.strip() == '[ dihedrals ]':
                        if line22.replace(" ", "") in dihedrals_list:
                            topology_content_dihedrals2 += line22
                            break

                for line22 in topology_bak_file:
                    if line22.strip() in ['\n', '\r\n']:
                        if line22.replace(" ", "") not in dihedrals_list:
                            break
                    try:
                        if line22.replace(" ", "") not in dihedrals_list:
                            if (line22.split()[0].isdigit()):
                                topology_content_dihedrals2 += "    " + line22

                        else:
                            if line22.replace(" ", "") not in dihedrals_list:
                                if (line22.split()[0].isdigit()):
                                    topology_content_dihedrals2 += line22

                    except IndexError:
                        pass
        topology_content_dihedrals_filtered = '\n'.join(topology_content_dihedrals2.split('\n')[:-2])
        # print "adding topology file contents are"
        # print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
        with open(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "complex.itp",
                  "w") as new_topology_file:
            new_topology_file.write(topology_initial_content + "\n" +
                                    topology_content_atoms + topology_file_atoms_content + "\n" +
                                    topology_content_bonds + topology_file_bonds_content + "\n" +
                                    topology_content_pairs + topology_file_pairs_content + "\n" +
                                    topology_content_angles + topology_file_angles_content + "\n" +
                                    topology_content_dihedrals + topology_file_dihedrals_content + "\n" + topology_content_dihedrals_filtered)

        atoms_final_count = atoms_lastcount


    #--------------------   update INPUT.dat file ---------------------------------

    # =======================  get user input temperature  ============================
    key_name_temperature = "preliminary_temp_value"
    ProjectToolEssentials_res_temperature_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_temperature).latest('entry_time')
    temperature_input = ProjectToolEssentials_res_temperature_input.key_values
    # ======================= End of get user input temperature  ======================

    # =======================  get user input threads  ============================
    key_name_mmpbsa_threads_input = "catmec_mmpbsa_threads_input"
    ProjectToolEssentials_res_key_name_mmpbsa_threads_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_mmpbsa_threads_input).latest('entry_time')
    catmec_mmpbsa_threads_input = ProjectToolEssentials_res_key_name_mmpbsa_threads_input.key_values
    # ======================= End of get user input threads  ======================

    new_input_lines = ""
    itp_ligand = "ligand.itp"
    itp_receptor = "complex.itp"
    with open(config.PATH_CONFIG['shared_scripts'] +"CatMec/Analysis/MMPBSA/"+"INPUT.dat") as mmpbsa_input_file:
        for line in mmpbsa_input_file:
            if ("\titp_ligand" in line):
                line = "\titp_ligand  " + itp_ligand + "\n"
                new_input_lines += line
            elif ("\titp_receptor" in line):
                line = "\titp_receptor  " + itp_receptor + "\n"
                new_input_lines += line
            elif ("temp" in line):
                line = "temp\t\t\t\t\t" + temperature_input + "\n"
                new_input_lines += line
            elif ("mnp" in line):
                line = "mnp\t\t\t\t\t" + catmec_mmpbsa_threads_input + "\n"
                new_input_lines += line
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)

#Designer trajconv
def perform__designer_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file):
    group_project_name = get_group_project_name(str(project_id))
    '''
                                                                              .                o8o
                                                                    .o8                `"'
                     .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .ooooo.  ooo. .oo.   oooo    ooo
                    888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 d88' `88b `888P"Y88b   `88.  .8'
                    888   888   888   888   888     Y888'           888    888         888 888       888   888  888   888    `88..8'
                    `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 888   888  888   888     `888'
                    `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y8bod8P' o888o o888o     `8'
                    d"     YD                                                          888
                    "Y88888P'                                                      .o. 88P
                                                                                   `Y888P
                    '''
    # create input file for trjconv command
    file_gmx_trjconv_input = open(config.PATH_CONFIG[
                                      'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + config.PATH_CONFIG[
                                      'designer_md_simulations_path'] + "gmx_trjconv_input.txt", "w")
    file_gmx_trjconv_input.write("1 \n24 \n ")
    file_gmx_trjconv_input.close()
    time.sleep(3)
    '''gmx_trjconv = "gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
                  config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                      'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                      'md_simulations_path'] + "gmx_trjconv_input.txt"'''

    os.system("gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+  project_name + '/Designer/' + \
              config.PATH_CONFIG['designer_mmpbsa_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/Designer/' + config.PATH_CONFIG[
                  'designer_mmpbsa_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + "gmx_trjconv_input.txt")

#designer module process mmpbsa input file
def pre_process_designer_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input):
    group_project_name = get_group_project_name(str(project_id))

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.key_values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/topol.top") as topol_file:
        for line in topol_file:
            if line.strip() == '[ atoms ]':  # start from atoms section
                break
        for line in topol_file:  # End at bonds sections
            if line.strip() == '[ bonds ]':
                break
            count_line += 1
            if line not in ['\n', '\r\n']: # remove new lines and empty lines
                line_list.append(line)  # line[:-1]
    atoms_final_count = line_list[-1].split()[0]
    #==================== End of get ATOMS final count  ===========================
    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
        if ligand_inputvalue.split("_")[0] != ligand_name: # Filter with user input ligand
            initial_text_content = ""
            topology_file_atoms_content = ""
            topology_file_bonds_content = ""
            topology_file_pairs_content = ""
            topology_file_angles_content = ""
            topology_file_dihedrals_content = ""
            topology_content_atoms = ""
            topology_content_bonds = ""
            topology_content_pairs = ""
            topology_content_angles = ""
            topology_content_dihedrals = ""
            topology_initial_content = ""

            atoms_lastcount = atoms_final_count
            # initial_text_content = initial_text_content+itp_file_inp[:-4]
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
                for line2 in itp_file:
                    if line2.strip() == '[ atoms ]':
                        initial_text_content += line2
                        break
                    initial_text_content += line2
                for line2 in itp_file:
                    if line2.strip() == '[ bonds ]':
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            atoms_lastcount = int(line2.split()[0]) + int(atoms_final_count)
                            line2 = line2.replace(line2.split()[0], str(int(line2.split()[0]) + int(atoms_final_count)),
                                                  1)
                            line2 = line2.lstrip()
                            initial_text_content += "    " + line2
                            topology_file_atoms_content += "    " + line2
                        else:
                            initial_text_content += line2
                            topology_file_atoms_content += line2
                    except IndexError:
                        pass

            # append edited data fo bonds section
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
                for line2 in itp_file:
                    if line2.strip() == '[ bonds ]':
                        initial_text_content += "\n" + line2
                        break
                for line2 in itp_file:
                    if line2.strip() == '[ pairs ]':
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            # pat = re.compile("^\S(.*\S)?$")
                            line2 = line2.replace(line2.split()[0], str(int(line2.split()[0]) + int(atoms_final_count)),
                                                  1)
                            line2 = line2.replace(" " + line2.split()[1] + " ",
                                                  str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                            line2 = line2.lstrip()
                            initial_text_content += "    " + line2
                            topology_file_bonds_content += "    " + line2
                        else:
                            initial_text_content += line2
                            topology_file_bonds_content += line2
                    except IndexError:
                        pass

            # append edited data for pairs section
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
                for line2 in itp_file:
                    if line2.strip() == '[ pairs ]':
                        initial_text_content += "\n" + line2
                        break
                for line2 in itp_file:
                    if line2.strip() == '[ angles ]':
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            # pat = re.compile("^\S(.*\S)?$")
                            line2 = line2.replace(line2.split()[0], str(int(line2.split()[0]) + int(atoms_final_count)),
                                                  1)
                            line2 = line2.replace(" " + line2.split()[1] + " ",
                                                  str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                            line2 = line2.lstrip()
                            initial_text_content += "    " + line2
                            topology_file_pairs_content += "    " + line2
                        else:
                            initial_text_content += line2
                            topology_file_pairs_content += line2
                    except IndexError:
                        pass

                        # append edited data for angles section
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
                for line2 in itp_file:
                    if line2.strip() == '[ angles ]':
                        initial_text_content += "\n" + line2
                        break
                for line2 in itp_file:
                    if line2.strip() == '[ dihedrals ]':
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            # pat = re.compile("^\S(.*\S)?$")
                            line2 = line2.replace(line2.split()[0], str(int(line2.split()[0]) + int(atoms_final_count)),
                                                  1)
                            line2 = line2.replace(" " + line2.split()[1] + " ",
                                                  str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                            line2 = line2.replace(" " + line2.split()[2] + " ",
                                                  str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                            line2 = line2.lstrip()
                            initial_text_content += "    " + line2
                            topology_file_angles_content += "    " + line2
                        else:
                            initial_text_content += line2
                            topology_file_angles_content += line2
                    except IndexError:
                        pass

                        # apend edited data for dihedrals section
            with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                          'designer_md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
                for line2 in itp_file:
                    if line2.strip() == '[ dihedrals ]':
                        initial_text_content += "\n" + line2
                        break

                for line2 in itp_file:
                    if line2.strip() == '\n':
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            # pat = re.compile("^\S(.*\S)?$")
                            line2 = line2.replace(line2.split()[0], str(int(line2.split()[0]) + int(atoms_final_count)),
                                                  1)
                            line2 = line2.replace(" " + line2.split()[1] + " ",
                                                  str(int(line2.split()[1]) + int(atoms_final_count)), 1)
                            line2 = line2.replace(" " + line2.split()[2] + " ",
                                                  str(int(line2.split()[2]) + int(atoms_final_count)), 1)
                            line2 = line2.replace(" " + line2.split()[3] + " ",
                                                  str(int(line2.split()[3]) + int(atoms_final_count)), 1)
                            line2 = line2.lstrip()
                            initial_text_content += "    " + line2
                            topology_file_dihedrals_content += "    " + line2
                        else:
                            initial_text_content += line2
                            topology_file_dihedrals_content += line2
                    except IndexError:
                        pass

            # ================================================================================================
            # ====================================== TOPOLOGY FILE ===========================================
            # ================================================================================================
            # write respective contents to topology file
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ atoms ]':
                        topology_content_atoms += line2
                        break
                    topology_initial_content += line2
                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_atoms += "    " + line2
                        else:
                            topology_content_atoms += line2
                    except IndexError:
                        pass

            # ===================  bonds content  ===========================
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ bonds ]':
                        topology_content_bonds += line2
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_bonds += "    " + line2
                        else:
                            topology_content_bonds += line2
                    except IndexError:
                        pass

            # ==================   pairs content  ===============================
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ pairs ]':
                        topology_content_pairs += line2
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_pairs += "    " + line2
                        else:
                            topology_content_pairs += line2
                    except IndexError:
                        pass

            # =======================   angles content   ==============================
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ angles ]':
                        topology_content_angles += line2
                        break

                for line2 in topology_bak_file:
                    if re.search(r"\[(\s\w+\s)\]", line2):
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_angles += "    " + line2
                        else:
                            topology_content_angles += line2
                    except IndexError:
                        pass

            # ======================   dihedrals content   ========================
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ dihedrals ]':
                        topology_content_dihedrals += line2
                        break

                for line2 in topology_bak_file:
                    if line2.strip() == "\n":
                        break
                    try:
                        if (line2.split()[0] != ";"):
                            topology_content_dihedrals += "    " + line2
                        else:
                            topology_content_dihedrals += line2
                    except IndexError:
                        pass
            print("adding topology file contents are")
            print(topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n")
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "complex.itp", "w") as new_topology_file:
                new_topology_file.write(topology_initial_content + "\n" +
                                        topology_content_atoms + topology_file_atoms_content + "\n" +
                                        topology_content_bonds + topology_file_bonds_content + "\n" +
                                        topology_content_pairs + topology_file_pairs_content + "\n" +
                                        topology_content_angles + topology_file_angles_content + "\n" +
                                        topology_content_dihedrals + topology_file_dihedrals_content)

            atoms_final_count = atoms_lastcount
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+"new_" +ligand_inputvalue.split("_")[0]+".itp", "w") as new_itp_file:
                new_itp_file.write(initial_text_content)

    #--------------------   update INPUT.dat file ---------------------------------
    new_input_lines = ""
    itp_ligand = "ligand.itp"
    itp_receptor = "complex.itp"
    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+"INPUT.dat") as mmpbsa_input_file:
        for line in mmpbsa_input_file:
            if ("\titp_ligand" in line):
                line = "\titp_ligand  " + itp_ligand + "\n"
                new_input_lines += line
            elif ("\titp_receptor" in line):
                line = "\titp_receptor  " + itp_receptor + "\n"
                new_input_lines += line
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)


class pathanalysis(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        # Path analysis for CatMec and Designer modules
        # Check for Command Title
        if commandDetails_result.command_title == "CatMec":
            # Execute for CatMec module
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string)
            # change working directory
            try:
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
            except:  # except path error
                # create directory
                os.system("mkdir " + config.PATH_CONFIG[
                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                # change directory
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)

            #copy PDB frames from CatMec Analysis Contact Score module
            #catmec contact score path
            catmec_contact_score_path = config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/Contact_Score/'
            for dir_files in listdir(catmec_contact_score_path):
                if dir_files.endswith(".pdb"):  # applying .tpr file filter
                    shutil.copyfile(catmec_contact_score_path+dir_files,config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool+"/"+dir_files)

            #copy execution files (scripts)
            for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
                shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'+script_dir_file,config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool+"/"+script_dir_file)

            # execute PathAnalysis command
            process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string)
                print(JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode}))
            if process_return.returncode != 0:
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string)
                print(JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode}))

        else:
            # Execute for Designer module Path Analysis
            #update command status to initiated
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string)

            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + '/mutated_list.txt', 'r') as fp_mutated_list:
                mutated_list_lines = fp_mutated_list.readlines()
                variant_index_count = 0
                for line_mutant in mutated_list_lines:
                    # line_mutant ad mutation folder
                    primary_command_runnable = commandDetails_result.primary_command
                    # change working directory
                    try:
                        os.chdir(config.PATH_CONFIG[
                                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                    except OSError as e:  # excep path error
                        error_num, error_msg = e
                        if error_msg.strip() == "The system cannot find the file specified":
                            # create directory
                            os.system("mkdir " + config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                            # change directory
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                    # IN LOOP
                    # copy PDB frames from Designer Analysis Contact Score module
                    # contact score path
                    designer_queue_contact_score_path = config.PATH_CONFIG[
                                                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Contact_Score/'
                    for dir_files in listdir(designer_queue_contact_score_path):
                        if dir_files.endswith(".pdb"):
                            shutil.copyfile(designer_queue_contact_score_path + dir_files, config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Path_Analysis/' + dir_files)

                    # copy execution files (scripts)
                    for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
                        shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/' + script_dir_file,
                                        config.PATH_CONFIG[
                                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Path_Analysis/' + script_dir_file)

                    # run Path analysis last executed command(executed in CatMec module)
                    os.system(commandDetails_result.primary_command)

#designer path analysis for SLURM
def designer_slurm_queue_path_analysis(request, md_mutation_folder, project_name, command_tool, project_id,
                                             user_id,inp_command_id,contact_score_job_id):
    group_project_name = get_group_project_name(str(project_id))

    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')

    shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Designer/designer_pathanalysis__slurm_pre_processing.py',
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/designer_pathanalysis__slurm_pre_processing.py")
    shutil.copyfile(config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/designer_pathanalysis__slurm_pre_processing.py",
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Path_Analysis/designer_pathanalysis__slurm_pre_processing.py")
    # =======   get assigned server for project ============
    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values
    initial_string = 'QZW'
    module_name = 'Designer_path_analysis'
    job_name = initial_string + '_' + str(
        project_id) + '_' + project_name + '_' + 'mutation_' + md_mutation_folder + '_' + module_name
    dest_file_path = config.PATH_CONFIG['local_shared_folder_path'] + project_name + "/" + command_tool
    number_of_threads = 4
    generate_designer_path_analysis_slurm_script(dest_file_path, server_value, job_name, number_of_threads,
                                                 inp_command_id,
                                                 md_mutation_folder, project_name, command_tool, project_id, user_id)

    # basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    # windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'

    print("Converting from windows to unix format")
    os.system("perl -p -e 's/\r$//' < " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + "basic_sbatch_script_windows_format.sh > " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Path_Analysis/" + "path_analysis_sbatch.sh")
    print('queuing **********************************************************************************')

    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/Analysis/Path_Analysis/")
    cmd = "sbatch --dependency=afterok:" + contact_score_job_id + " " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Path_Analysis/" + "path_analysis_sbatch.sh"
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
    except db.OperationalError as e:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in except of contact score SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")
    return job_id



#designer queue  path analysis
def designer_queue_path_analysis(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    primary_run_command = ""
    input_atom_number = ""
    ''' (SAGAR) commented on 14-08-2019 to fetch new parameters(from CatMec module ) from database
    commandDetails_result = commandDetails.objects.get(project_id=project_id,user_id=user_id,command_tool='Path_Analysis',command_title='CatMec').latest('entry_time')'''
    try:
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
    except OSError as e:  # except path error
        error_num, error_msg = e
        if error_msg.strip() == "The system cannot find the file specified":
            # create directory
            os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
            # change directory
            os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
    # copy PDB frames from Designer Analysis Contact Score module
    # contact score path
    designer_queue_contact_score_path = config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Contact_Score/'
    for dir_files in listdir(designer_queue_contact_score_path):
        if dir_files.endswith(".pdb"):
            shutil.copyfile(designer_queue_contact_score_path + dir_files, config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/'+ dir_files)

    # copy execution files (scripts)
    for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
        shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/' + script_dir_file, config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/'+ script_dir_file)

    #get path_analysis parameters from database
    ProjectToolEssentials_res_catmec_pathanalysis = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name='catmec_path_analysis_input_atom_starting_point').latest('entry_time')
    #catmec_pathanalysis_atom_input = ProjectToolEssentials_res_catmec_pathanalysis.values
    catmec_pathanalysis_atom_input = ast.literal_eval(ProjectToolEssentials_res_catmec_pathanalysis.key_values)
    chain_id_input = ""
    recidue_number_input = ""
    probe_radius_input = ""
    for inputkey, inputvalue in catmec_pathanalysis_atom_input.iteritems():
        if inputkey == "chain_id":
            chain_id_input = inputvalue
        if inputkey == "recidue_number":
            recidue_number_input = inputvalue
        if inputkey == "probe_radius":
            probe_radius_input = inputvalue
    #open PDB file to get atom number based on CatMec module path analysis
    pdb_file_path = config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/frames_0.pdb'
    with open(pdb_file_path) as pdb_frame:
        lines = pdb_frame.readlines()
        for line in lines:
            ''' PDB PARSER
                   ATOM / HETAATM  STRING line[0:6]
                   INDEX           STRING line[6:11]
                   ATOM TYPE       STRING line[12:16]
                   AMINO ACID      STRING line[17:20]
                   CHAIN ID        STRING line[21:22]
                   RESIDUE NO      STRING line[22:26]
                   X CO-ORDINATE   STRING line[30:38]
                   Y CO-ORDINATE   STRING line[38:46]
                   Z CO-ORDINATE   STRING line[46:54]
                   '''
            if line[0:6].strip() == "ATOM" or line[0:6].strip() == "HETAATM":
                if line[21:22].stripi() == str(chain_id_input) and line[22:26].strip() == str(recidue_number_input):
                    input_atom_number = str(line[6:11].strip())

    primary_run_command = "python3 perform_path_analysis.py "+probe_radius_input+" "+input_atom_number
    #run Path analysis last executed command(executed in CatMec module)
    os.system(primary_run_command)


#Extract Activation energy
class get_activation_energy(APIView):
    def get(self,request):
        pass

    def post(self,request):
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/')
        print(os.system("pwd"))
        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)
        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)
        if process_return.returncode == 0:
            print("inside success")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails.command_tool,commandDetails.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("inside error")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails.command_tool,commandDetails.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

class Hello_World(APIView):
    def get(self,request):
        pass
    def post(self,request):
        print ("Hello World")
        inp_command_id = 2599
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        time.sleep(3)
        try:
            django_logger.info("Hey there it works!! and in post is"+str(request.POST)+"\nend of post data")
            django_logger.debug("Hey there it works!! and in post is" + str(request.POST) + "\nend of post data")
            print("<<<<<<<<<<<<<<<<<<<<<<< in try >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            print("project name after sleep is ")
            print(project_name)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
            return JsonResponse({'success': True})
        except db.OperationalError as e:
            print("<<<<<<<<<<<<<<<<<<<<<<< in except >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            db.close_old_connections()
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            print("project name after sleep is ")
            print(project_name)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
            return JsonResponse({'success': True})


class Execute_Command(APIView):
    def get(self,request):
        pass
    def post(self,request):
        print ("*************user direct command execution****************88")
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))
        command_comment = commandDetails_result.comments
        command_tool = command_comment.split("#+#")[0]
        command_title = command_comment.split("#+#")[1]
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + group_project_name + "/" + str(project_name) + '/' + str(command_tool) + '/' +
                 str(command_title))
        print(os.system("pwd"))
        program_path = config.PATH_CONFIG['local_shared_folder_path'] + group_project_name + "/" + str(
            project_name) + '/' + str(command_tool) + '/' + str(command_title)+'/'
        process_return = execute_fjs_command(primary_command_runnable, inp_command_id,program_path,command_title,user_email_string,project_name, project_id, command_tool)
        out, err = process_return.communicate()
        process_return.wait()
        if process_return.returncode == 0:
            print("Success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name + "/" + str(
                project_name) + '/' + str(command_tool) + '/' + str(command_title) + '/' + str(command_title) + '_final.log',
                           'w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("Error in executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name + "/" + str(
                project_name) + '/' + str(command_tool) + '/' + str(command_title) + '/' + str(command_title) + '_final.log',
                           'w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

class mmpbsa(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))


        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/')
        print(os.system("pwd"))
        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name, project_id, commandDetails.command_tool,commandDetails.command_title)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)
        if process_return.returncode == 0:
            print("inside success")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails.command_tool,commandDetails.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("inside error")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


def designer_slurm_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id,mmpbsa_job_id,inp_command_id):
    group_project_name = get_group_project_name(str(project_id))
    #create directory
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/")
    # copy python processing file for contact_score

    shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Designer/designer_contactscore__slurm_pre_processing.py',
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/designer_contactscore__slurm_pre_processing.py")
    shutil.copyfile(config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/designer_contactscore__slurm_pre_processing.py",
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/designer_contactscore__slurm_pre_processing.py")

    #------- get number of threads input for contact score -----------
    command_tootl_title = 'Contact_Score'
    ProjectToolEssentials_res_catmec_contact_score = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                   key_name='catmec_contact_score').latest('entry_time')
    catmec_contact_score_dict = ast.literal_eval(ProjectToolEssentials_res_catmec_contact_score.key_values)
    for inputkey, inputvalue in catmec_contact_score_dict.iteritems():
        if inputkey == 'no_of_threads':
            number_of_threads = inputvalue
    #------- end of get number of threads input for contact score --------
    # =======   get assigned server for project ============
    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values
    initial_string = 'QZW'
    module_name = 'Designer_contact_score'
    job_name = initial_string + '_' + str(
        project_id) + '_' + project_name + '_' + 'mutation_' + md_mutation_folder + '_' + module_name
    dest_file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool

    generate_designer_contact_score_slurm_script(dest_file_path, server_value, job_name, number_of_threads, inp_command_id,
                                   md_mutation_folder, project_name, command_tool, project_id, user_id)

    # basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    # windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'

    print("Converting from windows to unix format")
    os.system("perl -p -e 's/\r$//' < " + config.PATH_CONFIG[
        'local_shared_folder_path'] + group_project_name+"/"+project_name + "/" + command_tool + "/" + "basic_sbatch_script_windows_format.sh > " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/" + "contact_score_sbatch.sh")
    print('queuing **********************************************************************************')

    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/")
    cmd = "sbatch --dependency=afterok:" + mmpbsa_job_id + " " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/" + "contact_score_sbatch.sh"
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
    except db.OperationalError as e:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in except of contact score SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")
    return job_id

def designer_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    entry_time = datetime.now()
    try:
        # ======= change working directory ==========
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/" )
    except OSError as e:  # excep path error
        error_num, error_msg = e
        if error_msg.strip() == "The system cannot find the file specified":
            # =========  create directory  ==========
            os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/")
            # =========   change directory  =========
            os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/")

    # =======   create PDBS folder ==============
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/pdbs/")

    # ---------  generate PDB frames from .XTC file   ----------------
    key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
    ProjectToolEssentials_protien_ligand_complex_index_number = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_protien_ligand_complex_index_number).latest(
            'entry_time')
    index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.key_values

    # ------   get TPR file   ------
    # get .tpr file from MD Simulations mutations folder(key = designer_mmpbsa_tpr_file)
    key_name_tpr_file = 'designer_mmpbsa_tpr_file'

    ProjectToolEssentials_res_tpr_file_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_tpr_file).latest('entry_time')
    md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.key_values.replace('\\', '/')

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG[
            'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n "+config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG[
            'mmpbsa_project_path'] +"trial/index.ndx    ")

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_center.xtc -s " +
        config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o merged_fit.xtc -fit rot+trans -n")

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_fit.xtc -s " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+'Analysis/Contact_score' + "/frames_.pdb -split 1 -n")

    #copy python scripts (shared_scripts)
    shutil.copyfile(config.PATH_CONFIG[
            'shared_scripts'] +"Contact_Score/readpdb2.py",config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+'Analysis/Contact_score/readpdb2.py')
    shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + "Contact_Score/whole_protein_contact.py", config.PATH_CONFIG[
        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + 'Analysis/Contact_score/whole_protein_contact.py')

    #  ==========  get new contact score parameters from DB   =========================
    command_tootl_title = 'Contact_Score'
    ProjectToolEssentials_res_catmec_contact_score = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                   key_name='catmec_contact_score').latest('entry_time')
    designer_contact_score_cmd_calculate = ""
    designer_contact_score_cmd_combine = ""
    catmec_contact_score_dict = ast.literal_eval(ProjectToolEssentials_res_catmec_contact_score.key_values)
    for inputkey, inputvalue in catmec_contact_score_dict.iteritems():
        if inputkey == 'command':
            designer_contact_score_cmd_calculate = inputvalue
            designer_contact_score_cmd_combine = designer_contact_score_cmd_calculate.replace(" C "," S ")
    #get contact_score parameters from DB
    ''' (SAGAR) commented on 14-08-2019 to fetch new details of contact score command from database
    project_commands = commandDetails.objects.all().filter(project_id=project_id,
                                                                          command_title="CatMec",
                                                                          command_tool="Contact_Score",
                                                                          user_id=user_id).order_by("-command_id")
    print("0 th contact score command")
    print(project_commands[0].primary_command)
    print("1 th contact score command")
    print(project_commands[1].primary_command)'''
    # execute contact score command
    # change to contact score working directory
    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/")
    os.system(designer_contact_score_cmd_calculate)
    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + "/" + md_mutation_folder + "/Analysis/Contact_score/")
    os.system(designer_contact_score_cmd_combine)


class Contact_Score(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        #Contact Score calculation for CatMec and Designer modules
        #Check for Command Title
        if commandDetails_result.command_title == "CatMec":
            #Execute for CatMec module
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            primary_command_runnable = commandDetails_result.primary_command

            # check command IF Contact calculation(C) or combine contact score(S)
            if primary_command_runnable.split()[3].strip() == "C":
                # change working directory
                try:
                    os.chdir(config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                except:  # excep path error
                    # error_num, error_msg = e
                    # if error_msg.strip() == "The system cannot find the file specified":
                    # create directory
                    os.system("mkdir " + config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                    # change directory
                    os.chdir(config.PATH_CONFIG[
                                 'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)

                # copy Contact Score python scripts
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Contact_Score/whole_protein_contact.py',
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/" + "whole_protein_contact.py")

                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Contact_Score/readpdb2.py',
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/" + "readpdb2.py")

                # ------   create PDBS folder -----------
                os.system("mkdir " + config.PATH_CONFIG[
                    'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/pdbs")

                # ---------  generate PDB frames from .XTC file   ----------------
                key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
                ProjectToolEssentials_protien_ligand_complex_index_number = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_protien_ligand_complex_index_number).latest(
                        'entry_time')
                index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.key_values

                # ------   get TPR file   ------
                # get .tpr file from MD Simulations(key = mmpbsa_tpr_file)
                key_name_tpr_file = 'mmpbsa_tpr_file'

                ProjectToolEssentials_res_tpr_file_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_tpr_file).latest('entry_time')
                md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.key_values.replace('\\', '/')
                md_simulations_tpr_file_split = md_simulations_tpr_file.split("/")

                # create trajconv input file
                file_gmx_trajconv_input = open("gmx_trajconv_input.txt", "w")
                file_gmx_trajconv_input.write("1\n0\nq")
                file_gmx_trajconv_input.close()

                os.system(
                    "gmx trjconv -f " + config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                        'md_simulations_path'] + md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/' +config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "trial/index.ndx < gmx_trajconv_input.txt")

                '''os.system(
                    "gmx trjconv -f merged_center.xtc -s " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                        'md_simulations_path'] + md_simulations_tpr_file + " -o merged_fit.xtc -fit rot+trans -n "+config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] +"complex_index.ndx < gmx_trajconv_input.txt")'''

                os.system(
                    "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_center.xtc -s " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                        'md_simulations_path'] + md_simulations_tpr_file + " -o " + config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/frames_.pdb -split 0 -sep -n " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "trial/index.ndx ")
            else: # primary_command_runnable.split()[3].strip() == "S":
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                print("------   in contact score combine ----------")
                pass

            print("primary_command_runnable is -------------")
            print(primary_command_runnable)
            #execute contact score command
            print(os.system(primary_command_runnable))
            return JsonResponse({"success": True})
            '''
            .-,--.                                          .     .      
            ' |   \ ,-. ,-. . ,-. ,-. ,-. ,-.   ,-,-. ,-. ,-| . . |  ,-. 
            , |   / |-' `-. | | | | | |-' |     | | | | | | | | | |  |-' 
            `-^--'  `-' `-' ' `-| ' ' `-' '     ' ' ' `-' `-' `-' `' `-' 
                               ,|                                        
                               `'                                        
            '''
        elif commandDetails_result.command_title == "Designer": #Designer module
            #Execute for Designer module
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            with open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + '/mutated_list.txt', 'r') as fp_mutated_list:
                mutated_list_lines = fp_mutated_list.readlines()
                variant_index_count = 0
                for line_mutant in mutated_list_lines:
                    # line_mutant ad mutation folder
                    # change working directory
                    try:
                        os.chdir(config.PATH_CONFIG[
                                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")
                    except OSError as e:  # excep path error
                        error_num, error_msg = e
                        if error_msg.strip() == "The system cannot find the file specified":
                            # create directory
                            os.system("mkdir " + config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")
                            # change directory
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")

                    # ------   create PDBS folder -----------
                    os.system("mkdir " + config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/pdbs/")

                    # ---------  generate PDB frames from .XTC file   ----------------
                    key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
                    ProjectToolEssentials_protien_ligand_complex_index_number = \
                        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                   key_name=key_name_protien_ligand_complex_index_number).latest(
                            'entry_time')
                    index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.key_values

                    # ------   get TPR file   ------
                    # get .tpr file from MD Simulations mutations folder(key = designer_mmpbsa_tpr_file)
                    key_name_tpr_file = 'designer_mmpbsa_tpr_file'

                    ProjectToolEssentials_res_tpr_file_input = \
                        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                   key_name=key_name_tpr_file).latest('entry_time')
                    md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.key_values.replace('\\', '/')

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f " + config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" +
                        config.PATH_CONFIG[
                            'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n")

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_center.xtc -s " +
                        config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o merged_fit.xtc -fit rot+trans -n")

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_fit.xtc -s " + config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o " +
                        config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score' + "/frames_.pdb -split 1 -n")

                    # copy python scripts (shared_scripts)
                    shutil.copyfile(config.PATH_CONFIG[
                                        'local_shared_folder_path'] + "Contact_Score/readpdb2.py", config.PATH_CONFIG[
                                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score/readpdb2.py')
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + "Contact_Score/whole_protein_contact.py",
                                    config.PATH_CONFIG[
                                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score/whole_protein_contact.py')

                    #execute Contact Score primary command
                    os.chdir(config.PATH_CONFIG[
                                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score/')
                    os.system(commandDetails_result.primary_command)
        else:
            pass

def sol_group_option():
    print("=====================working directory in function is ==============")
    print(os.getcwd())
    log_file = "gromacs_solve_gro_indexing.txt"
    string_data = " SOL "
    matched_data = ""

    log_file_buffer = open(log_file, "r")

    for lines in log_file_buffer.readlines():
        # print "printing 1st loop"
        lines_data = lines
        if string_data in lines_data:
            matched_data = lines
            print(matched_data)
    SOL_option_value = matched_data
    SOL_option_value = SOL_option_value.split()
    print(SOL_option_value)
    return SOL_option_value


def md_simulation_minimization(project_id,project_name,command_tool,number_of_threads,md_simulation_path='',designer_module=True):
    group_project_name = get_group_project_name(str(project_id))
    # EXECUTION OF GROMACS FUNCTION UNTIL MINIMIZATION IN MD SIMULATION DIRECTORY
    if designer_module:
        source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + "/"+command_tool + "/"+str(md_simulation_path)+"/"
    else:
        source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + md_simulation_path
    os.chdir(source_file_path)
    print("start editconf==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    print("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
    print("gmx grompp -f vac_em.mdp -po mdout.mdp -c newbox.gro -p topol.top -r newbox.gro -o vac_em.tpr -maxwarn 2")
    print("gmx mdrun -v -s vac_em.tpr -o vac_em.trr -cpo vac_em.cpt -c vac_em.gro -e vac_em.edr -g vac_em.log -deffnm vac_em -nt " + str(number_of_threads))
    os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
    os.system("gmx grompp -f vac_em.mdp -po mdout.mdp -c newbox.gro -p topol.top -r newbox.gro -o vac_em.tpr -maxwarn 2")
    os.system("gmx mdrun -v -s vac_em.tpr -o vac_em.trr -cpo vac_em.cpt -c vac_em.gro -e vac_em.edr -g vac_em.log -deffnm vac_em -nt " + str(number_of_threads))

    print("gmx solvate -cp vac_em.gro -cs spc216.gro -p topol.top -o solve.gro")
    print("start solvate==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("gmx solvate -cp vac_em.gro -cs spc216.gro -p topol.top -o solve.gro")

    print("start make_ndx==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")

    print("start grompp 11111111111111111111==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")

    group_value = sol_group_option()
    SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
    SOL_replace_str = SOL_replace_backup
    SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value[0]))
    print("printing group value in MD$$$$$$$$$$$$$$$$$$")
    print(group_value)
    print("printing after %SOL% replace")
    print(SOL_replace_str)
    print("start genion ==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system(SOL_replace_str)

    print("echo q | gmx make_ndx -f solve_ions.gro")
    print("start make_ndx 222222222222 ==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("echo q | gmx make_ndx -f solve_ions.gro")

    print("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr -maxwarn 10")
    print("start grompp 222222222222 ==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr -maxwarn 10")

    print("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em  -nt "+str(number_of_threads))
    print("start mdrun  ==========================================")
    print('before change directory')
    print(os.getcwd())
    os.chdir(source_file_path)
    print('after change directory')
    print(os.getcwd())
    os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em -nt "+str(number_of_threads))


@csrf_exempt
def replace_temp_and_nsteps_in_mdp_file(file_path,  temp_value, nsteps_value):
    print('inside replace_temp_and_nsteps_in_mdp_file function')
    try:
        original_nvt_mdp_lines = ''
        original_npt_mdp_lines = ''
        original_md_mdp_lines = ''
        with open(file_path+'pre_nvt.mdp', 'r') as pre_processed_mdb:
            content = pre_processed_mdb.readlines()
            for line in content:
                if 'QZTEMP' in line:
                    original_nvt_mdp_lines += line.replace('QZTEMP', str(temp_value))
                else:
                    original_nvt_mdp_lines += line

        with open(file_path+'pre_npt.mdp', 'r') as pre_processed_mdb:
            content = pre_processed_mdb.readlines()
            for line in content:
                if 'QZTEMP' in line:
                    original_npt_mdp_lines += line.replace('QZTEMP', str(temp_value))
                else:
                    original_npt_mdp_lines += line

        with open(file_path+'pre_md.mdp', 'r') as pre_processed_mdb:
            content = pre_processed_mdb.readlines()
            for line in content:
                if 'QZTEMP' in line:
                    original_md_mdp_lines += line.replace('QZTEMP', str(temp_value))
                elif 'QZNSTEPS' in line:
                    original_md_mdp_lines += line.replace('QZNSTEPS', str(nsteps_value))
                else:
                    original_md_mdp_lines += line

        with open(file_path+'nvt.mdp', 'w+') as nvt_source_file:
            nvt_source_file.write(original_nvt_mdp_lines)

        with open(file_path+'npt.mdp', 'w+') as npt_source_file:
            npt_source_file.write(original_npt_mdp_lines)

        with open(file_path+'md.mdp', 'w+') as md_source_file:
            md_source_file.write(original_md_mdp_lines)
        return True
    except Exception as e:
        print('exception in replacing mdp file is ',str(e))
        return False


@csrf_exempt
def generate_slurm_script(file_path, server_name, job_name, number_of_threads):
    print('inside generate_slurm_script function')
    new_shell_script_lines = ''
    pre_simulation_script_file_name = 'pre_simulation.sh'
    simulation_script_file_name = 'simulation_windows_format.sh'
    print('before opening ',file_path +'/'+ pre_simulation_script_file_name)
    with open(file_path +'/'+ pre_simulation_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ pre_simulation_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ simulation_script_file_name):
        print('removing ',file_path + simulation_script_file_name)
        os.remove(file_path + '/' + simulation_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ simulation_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ simulation_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx -maxwarn 10 \n")
        new_bash_script.write("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt -nt "+str(number_of_threads)+"\n")
        new_bash_script.write("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx -maxwarn 10 \n")
        new_bash_script.write("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt -nt "+str(number_of_threads)+"\n")
        new_bash_script.write("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx -maxwarn 10 \n")
        new_bash_script.write("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1 -nt "+str(number_of_threads) + "\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True


@csrf_exempt
def generate_designer_slurm_script(file_path, server_name, job_name, number_of_threads,inp_command_id,md_mutation_folder,project_name,command_tool,project_id,user_id):
    group_project_name = get_group_project_name(str(project_id))
    print('inside generate_slurm_script function')
    new_shell_script_lines = ''
    basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'
    print('before opening ',file_path +'/'+ basic_sbatch_script_file_name)
    with open(file_path +'/'+ basic_sbatch_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ basic_sbatch_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ windows_format_script_file_name):
        print('removing ',file_path + windows_format_script_file_name)
        os.remove(file_path +'/'+ windows_format_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ windows_format_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ windows_format_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write("python designer_mmpbsa__slurm_pre_processing.py "+str(inp_command_id)+" "+str(md_mutation_folder)+" "+str(project_name)+" "+str(command_tool)+" "+str(project_id)+" "+str(user_id)+"\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True

def generate_designer_contact_score_slurm_script(file_path, server_name, job_name, number_of_threads,inp_command_id,md_mutation_folder,project_name,command_tool,project_id,user_id):
    group_project_name = get_group_project_name(str(project_id))
    print('inside generate_slurm_script function')
    new_shell_script_lines = ''
    basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'
    print('before opening ',file_path +'/'+ basic_sbatch_script_file_name)
    with open(file_path +'/'+ basic_sbatch_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ basic_sbatch_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ windows_format_script_file_name):
        print('removing ',file_path +'/'+ windows_format_script_file_name)
        os.remove(file_path +'/'+ windows_format_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ windows_format_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ windows_format_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write("python designer_contactscore__slurm_pre_processing.py "+str(inp_command_id)+" "+str(md_mutation_folder)+" "+str(project_name)+" "+str(command_tool)+" "+str(project_id)+" "+str(user_id)+"\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True



def generate_designer_path_analysis_slurm_script(file_path, server_name, job_name, number_of_threads,inp_command_id,md_mutation_folder,project_name,command_tool,project_id,user_id):
    print('inside generate_slurm_script function')
    new_shell_script_lines = ''
    basic_sbatch_script_file_name = 'basic_sbatch_script.sh'
    windows_format_script_file_name = 'basic_sbatch_script_windows_format.sh'
    print('before opening ',file_path +'/'+ basic_sbatch_script_file_name)
    with open(file_path +'/'+ basic_sbatch_script_file_name,'r') as source_file:
        print('inside opening ', file_path +'/'+ basic_sbatch_script_file_name)
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER',str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME',str(job_name)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS',str(number_of_threads)))
            else:
                new_shell_script_lines += line
    if os.path.exists(file_path +'/'+ windows_format_script_file_name):
        print('removing ',file_path +'/'+ windows_format_script_file_name)
        os.remove(file_path +'/'+ windows_format_script_file_name)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(file_path +'/'+ windows_format_script_file_name,'w+')as new_bash_script:
        print('opened ',file_path +'/'+ windows_format_script_file_name)
        new_bash_script.write(new_shell_script_lines+"\n")
        new_bash_script.write("python designer_pathanalysis__slurm_pre_processing.py "+str(inp_command_id)+" "+str(md_mutation_folder)+" "+str(project_name)+" "+str(command_tool)+" "+str(project_id)+" "+str(user_id)+"\n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
    print('outside the loop')
    return True

def prepare_mmpbsa_slurm_script(project_id,shared_dir_path,mmpbsa_project_path,project_name,server_name,job_title,mmpbsa_threads_input):
    group_project_name = get_group_project_name(str(project_id))
    # preparing windows format batch script for MMPBSA / Binding affinity calculation
    new_shell_script_lines = ''
    template_script = 'pre_simulation.sh'
    mmpbsa_shell_script = 'mmpbsa_windows_format.sh'
    with open(shared_dir_path + project_name + '/CatMec/MD_Simulation/'+ template_script, 'r') as source_file:
        content = source_file.readlines()
        for line in content:
            if 'QZSERVER' in line:
                new_shell_script_lines += (line.replace('QZSERVER', str(server_name)))
            elif 'QZJOBNAME' in line:
                new_shell_script_lines += (line.replace('QZJOBNAME', str(job_title)))
            elif 'QZTHREADS' in line:
                new_shell_script_lines += (line.replace('QZTHREADS', str(mmpbsa_threads_input)))
            else:
                new_shell_script_lines += line
    if os.path.exists(shared_dir_path +group_project_name+"/"+ project_name + '/CatMec/' +mmpbsa_project_path + mmpbsa_shell_script):
        os.remove(shared_dir_path +group_project_name+"/"+ project_name + '/CatMec/' +mmpbsa_project_path + mmpbsa_shell_script)
    # the below code depits final simulation batch script generation by opening in wb mode for not considering operating system of windows or unix type
    with open(shared_dir_path +group_project_name+"/"+ project_name + '/CatMec/' +mmpbsa_project_path + mmpbsa_shell_script, 'w+')as new_bash_script:
        new_bash_script.write(new_shell_script_lines + "\n")
        new_bash_script.write("sh "+config.PATH_CONFIG['GMX_run_file_one']+" \n")
        new_bash_script.write("sh "+config.PATH_CONFIG['GMX_run_file_two']+" \n")
        new_bash_script.write("sh "+config.PATH_CONFIG['GMX_run_file_three']+" \n")
        new_bash_script.write("rsync -avz /scratch/$SLURM_JOB_ID/* $SLURM_SUBMIT_DIR/")
        os.system(
            "perl -p -e 's/\r$//' < " + shared_dir_path +group_project_name+"/"+ project_name + "/CatMec/" + mmpbsa_project_path + mmpbsa_shell_script + " > " + shared_dir_path + project_name + "/CatMec/" + mmpbsa_project_path + "mmpbsa_batch.sh")
    return True

@csrf_exempt
def md_simulation_preparation(inp_command_id,project_id,project_name,command_tool,command_title, user_id='', md_simulation_path=''):
    group_project_name = get_group_project_name(str(project_id))
    print("inside md_simulation_preparation function")
    print("user id is ",user_id)
    status_id = config.CONSTS['status_initiated']
    QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
    email_id = QzEmployeeEmail_result.email_id
    dot_Str_val = email_id.split('@')[0]
    lenght_of_name_with_dots = len(dot_Str_val.split("."))
    user_email_string = ""
    for i in range(lenght_of_name_with_dots):
        user_email_string += dot_Str_val.split(".")[i] + " "

    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, command_tool,command_title)
    print("inside md_simulation_preparation function")
    key_name = 'md_simulation_no_of_runs'
    print('md_simulation_path is')
    print(md_simulation_path)
    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = int(ProjectToolEssentials_res.key_values)
    no_of_thread_key = "number_of_threads"
    ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=no_of_thread_key).latest(
        'entry_time')

    number_of_threads = int(ProjectToolEssentials_res.key_values)

    temp_key = "preliminary_temp_value"
    temp_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=temp_key).latest(
        'entry_time')

    temp_value = float(temp_ProjectToolEssentials_res.key_values)

    nsteps_key = "md_simulation_nsteps_value"
    nsteps_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=nsteps_key).latest(
        'entry_time')

    nsteps_value = int(nsteps_ProjectToolEssentials_res.key_values)
    """
    slurm_key = "md_simulation_slurm_selection_value"
    slurm_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=slurm_key).latest(
        'entry_time')
    
    slurm_value = slurm_ProjectToolEssentials_res.key_values


    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values
    """
    server_value = "anygpu"
    print("server value is ",server_value)
    print("number of threads is ",number_of_threads)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print(md_run_no_of_conformation)

    source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + str(md_simulation_path)
    print('source file path in md simulation preparation --------------')
    print(source_file_path)

    print('server_value,slurm_value --------------------------------------------')
    print(server_value,'\n', server_value)
    function_returned_value = replace_temp_and_nsteps_in_mdp_file(config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + '/' + config.PATH_CONFIG['md_simulations_path'], temp_value, nsteps_value)
    if function_returned_value:
        print('replace mdp file function returned true')
        md_simulation_minimization(project_id,project_name,command_tool,number_of_threads,md_simulation_path,designer_module=False)
        for i in range(int(md_run_no_of_conformation)):
            if not (os.path.exists(source_file_path + 'md_run' + str(i + 1))):
                print (source_file_path + 'md_run' + str(i + 1))
                os.mkdir(source_file_path + 'md_run' + str(i + 1))
            dest_file_path = source_file_path + 'md_run' + str(i + 1)
            # copying MD Simulation files in to md_run(1/2/3...) folder
            for file_name in os.listdir(source_file_path):
                try:
                    print("inside try")
                    shutil.copy(str(source_file_path) + file_name, dest_file_path)
                except IOError as e:
                    print("Unable to copy file. %s" % e)
                    pass
                except Exception:
                    print("Unexpected error:", sys.exc_info())
                    pass
            # if slurm_value == "yes":
            print('slurm value selected is yes')
            initial_string = 'QZW'
            # module_name = 'CatMec'
            module_name = 'MD_SIMULATION'
            # job_name = initial_string + '_' + str(project_name) + '_' + module_name + '_r' + str(md_run_no_of_conformation)
            job_name = str(initial_string) + '_' + module_name + '_r' + str(md_run_no_of_conformation)
            job_detail_string = module_name + '_r' + str(md_run_no_of_conformation)
            generate_slurm_script(dest_file_path, server_value, job_name, number_of_threads)

            print('after generate_slurm_script ************************************************************************')
            print('before changing directory')
            print(os.getcwd())
            print('after changing directory')
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            print("Converting from windows to unix format")
            print("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
            os.system("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
            print('queuing **********************************************************************************')
            cmd = "sbatch "+ dest_file_path + "/" + "simulation.sh"
            print("Submitting Job1 with command: %s" % cmd)
            status, jobnum = commands.getstatusoutput(cmd)
            print("job id is ", jobnum)
            print("status is ", status)
            print("job id is ", jobnum)
            print("status is ", status)
            print(jobnum.split())
            lenght_of_split = len(jobnum.split())
            index_value = lenght_of_split - 1
            print(jobnum.split()[index_value])
            job_id = jobnum.split()[index_value]
            # save job id
            job_id_key_name = "job_id"
            entry_time = datetime.now()
            try:
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                       project_id=project_id,
                                                                                       entry_time=entry_time,
                                                                                       job_id=job_id,
                                                                                       job_status="1",
                                                                                       job_title=job_name,
                                                                                       job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of MD SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")
            except Exception as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of MD SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print("exception is ",str(e))
                pass
                '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                                       project_id=project_id,
                                                                                       entry_time=entry_time,
                                                                                       values=job_id,
                                                                                       job_id=job_id)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")'''
            print('queued')
            """elif slurm_value == "No":
                print('slurm value selected is no')
                print("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx -maxwarn 10")
                print("start grompp 33333333333333  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx -maxwarn 10")


                print("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt  -nt "+str(number_of_threads))
                print("start mdrun 2222222222222  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt -nt "+str(number_of_threads))


                print("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx -maxwarn 10")
                print("start grompp 44444444444  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx -maxwarn 10")


                print("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt -nt "+str(number_of_threads))
                print("start mdrun 333333333333  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt -nt "+str(number_of_threads))


                print("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx -maxwarn 10")
                print("start grompp 5555555555  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx -maxwarn 10")


                print("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1 -nt "+str(number_of_threads))
                print("start mdrun 4444444444444  ==========================================")
                print('before change directory')
                print(os.getcwd())
                os.chdir(source_file_path + '/md_run' + str(i + 1))
                print('after change directory')
                print(os.getcwd())
                os.system("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1 -nt "+str(number_of_threads))"""

        return JsonResponse({'success': True})
    else:
        print('replace mdp file function returned False')
        return JsonResponse({'success': False})



def execute_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    group_project_name = get_group_project_name(str(project_id))
    job_id =""
    db.close_old_connections()
    print("in execute_md_simulation definition")
    key_name = 'md_simulation_no_of_runs'

    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = int(ProjectToolEssentials_res.key_values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print(md_run_no_of_conformation)
    no_of_thread_key = "number_of_threads"
    ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=no_of_thread_key).latest(
        'entry_time')

    number_of_threads = int(ProjectToolEssentials_res.key_values)
    print("number of threads is ",number_of_threads)
    # copy MDP files to working directory
    MDP_filelist = ['em', 'ions', 'md', 'npt', 'nvt','vac_em']
    for mdp_file in MDP_filelist:
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/' + mdp_file + '.mdp',
                        config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        +group_project_name+"/"+ project_name + '/' + command_tool + '/' +str(md_mutation_folder)+"/"+ mdp_file + '.mdp')

    source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + "/"+command_tool + "/"+str(md_mutation_folder)+"/"
    source_file_path2 = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + "/" + command_tool + "/" + str(
        md_mutation_folder)
    md_simulation_minimization(project_id,project_name,command_tool,number_of_threads,md_mutation_folder,designer_module=True)

    try:
        # =======   get slurm key from  database   ===========
        slurm_key = "md_simulation_slurm_selection_value"
        slurm_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                     key_name=slurm_key).latest(
            'entry_time')

        slurm_value = slurm_ProjectToolEssentials_res.key_values
    except db.OperationalError as e:
        db.close_old_connections()
        # =======   get slurm key from  database   ===========
        slurm_key = "md_simulation_slurm_selection_value"
        slurm_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                     key_name=slurm_key).latest(
            'entry_time')

        slurm_value = slurm_ProjectToolEssentials_res.key_values


    #=======   get assigned server for project ============
    server_key = "md_simulation_server_selection_value"
    server_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=server_key).latest(
        'entry_time')

    server_value = server_ProjectToolEssentials_res.key_values

    # ======= get temperature and MD simulation runs from DB ========
    temp_key = "preliminary_temp_value"
    temp_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                key_name=temp_key).latest(
        'entry_time')

    temp_value = float(temp_ProjectToolEssentials_res.key_values)

    nsteps_key = "md_simulation_nsteps_value"
    nsteps_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                  key_name=nsteps_key).latest(
        'entry_time')

    nsteps_value = int(nsteps_ProjectToolEssentials_res.key_values)

    # substitutung config values in MD simulations MDP files
    function_returned_value = replace_temp_and_nsteps_in_mdp_file(
        config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + '/' + config.PATH_CONFIG['md_simulations_path'],
        temp_value, nsteps_value)
    for i in range(int(md_run_no_of_conformation)):
        file_outpu_md = open("test_output_md_"+'md_run' + str(i + 1)+".txt", "w+")
        print (source_file_path + 'md_run' + str(i + 1))
        os.mkdir(source_file_path + 'md_run' + str(i + 1))
        dest_file_path = source_file_path + 'md_run' + str(i + 1)
        for file_name in os.listdir(source_file_path):
            try:
                print("inside try")
                shutil.copy(str(source_file_path) + file_name, dest_file_path)
            except IOError as e:
                print("Unable to copy file. %s" % e)
                pass
            except Exception:
                print("Unexpected error:", sys.exc_info())
                pass
        # if user has selected Slurm job scheduler
        if slurm_value == "yes":
            print('slurm value selected is yes')
            initial_string = 'QZW'
            module_name = 'Designer'
            job_name = initial_string + '_' + str(project_id) + '_' +project_name+'_'+'mutation_'+md_mutation_folder+'_'+module_name + '_r' + str(
                md_run_no_of_conformation)
            # =============== copy shell script template files to MD simulation directory ===========
            shutil.copyfile(config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + "/"+command_tool+"/"+"pre_simulation.sh",
                            dest_file_path+"/"+"pre_simulation.sh")
            shutil.copyfile(config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(
                project_name) + "/" + command_tool + "/" + "basic_sbatch_script.sh",
                            dest_file_path + "/" + "basic_sbatch_script.sh")
            # ================ End of copy shell script templates ===================================
            generate_slurm_script(dest_file_path, server_value, job_name, number_of_threads)
            print(
                'after generate_slurm_script ************************************************************************')
            print('before changing directory')
            print(os.getcwd())
            print('after changing directory')
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            print("Converting from windows to unix format")
            print("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
            os.system("perl -p -e 's/\r$//' < simulation_windows_format.sh > simulation.sh")
            print('queuing **********************************************************************************')
            cmd = "sbatch " + dest_file_path + "/" + "simulation.sh"
            print("Submitting Job1 with command: %s" % cmd)
            status, jobnum = commands.getstatusoutput(cmd)
            print("job id is ", jobnum)
            print("status is ", status)
            print("job id is ", jobnum)
            print("status is ", status)
            print(jobnum.split())
            lenght_of_split = len(jobnum.split())
            index_value = lenght_of_split - 1
            print(jobnum.split()[index_value])
            job_id = jobnum.split()[index_value]
            # save job id
            job_id_key_name = "job_id"
            entry_time = datetime.now()
            try:
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id)
                QzwSlurmJobDetails_save_job_id.save()
            except db.OperationalError as e:
                print(
                    "<<<<<<<<<<<<<<<<<<<<<<< in except of MD SIMULATION SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")
        else:
            print("in md_run loooppppp")
            print(source_file_path + '/md_run' + str(i + 1))
            os.chdir(source_file_path + '/md_run' + str(i + 1))

            print("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx -maxwarn 10")
            print("start grompp 33333333333333  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx -maxwarn 10")

            print("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
            print("start mdrun 2222222222222  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt -nt 18")

            print("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx -maxwarn 10")
            print("start grompp 44444444444  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx -maxwarn 10")

            print("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt -nt "+str(number_of_threads))
            print("start mdrun 333333333333  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt -nt "+str(number_of_threads))

            print("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx -maxwarn 10")
            print("start grompp 5555555555  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx -maxwarn 10")

            print(
                "gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
            print("start mdrun 4444444444444  ==========================================")
            print(os.getcwd())
            os.chdir(source_file_path + '/md_run' + str(i + 1))
            print(os.getcwd())
            os.system(
                "gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1 -nt "+str(number_of_threads))

    return job_id


#Run MD Simulations for Hotspot module
def execute_hotspot_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id,
                                                  user_id,variant_dir_md):
    group_project_name = get_group_project_name(str(project_id))

    # key_name = 'md_simulation_no_of_runs'
    #
    # ProjectToolEssentials_res = \
    #     ProjectToolEssentials.objects.all().filter(project_id=project_id,
    #                                                key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = 1 # int(ProjectToolEssentials_res.key_values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print(md_run_no_of_conformation)
    no_of_thread_key = "number_of_threads"

    try:
        ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=no_of_thread_key).latest(
            'entry_time')
    except db.OperationalError as e:
        db.close_old_connections()
        ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=no_of_thread_key).latest(
        'entry_time')

    number_of_threads = int(ProjectToolEssentials_res.key_values)
    print("number of threads is ",number_of_threads)
    # copy MDP files to working directory
    MDP_filelist = ['em', 'ions', 'md', 'npt', 'nvt']
    for mdp_file in MDP_filelist:
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/' + mdp_file + '.mdp',
                        config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        +group_project_name+"/"+ project_name + '/' + command_tool + '/' +str(md_mutation_folder)+"/"+variant_dir_md+"/"+ mdp_file + '.mdp')

    source_file_path = config.PATH_CONFIG['shared_folder_path'] +group_project_name+"/"+ str(project_name) + "/"+command_tool + "/"+str(md_mutation_folder)+"/"+variant_dir_md+"/"
    for i in range(int(md_run_no_of_conformation)):
        print (source_file_path + 'md_run' + str(i + 1))
        os.mkdir(source_file_path + 'md_run' + str(i + 1))
        dest_file_path = source_file_path + 'md_run' + str(i + 1)
        for file_name in os.listdir(source_file_path):
            try:
                print("inside try")
                shutil.copy(str(source_file_path) + file_name, dest_file_path)
            except IOError as e:
                print("Unable to copy file. %s" % e)
                pass
            except Exception:
                print("Unexpected error:", sys.exc_info())
                pass
        print(os.getcwd())
        os.chdir(source_file_path + '/md_run' + str(i + 1))
        print('after change directory')
        print(os.getcwd())
        os.chdir(source_file_path + '/md_run' + str(i + 1))
        os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
        #print(os.getcwd())
        #os.chdir(source_file_path + '/md_run' + str(i + 1))
        #print('after change directory')
        #print(os.getcwd())
        #os.system("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
        #print(os.getcwd())
        #os.chdir(source_file_path + '/md_run' + str(i + 1))
        #print('after change directory')
        #print(os.getcwd())
        #os.system("echo q | gmx make_ndx -f newbox.gro > gromacs_solve_gro_indexing.txt")

        #os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")

        #group_value = sol_group_option()
        #SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
        #SOL_replace_str = SOL_replace_backup
        #SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value[0]))
        #print("printing group value in MD$$$$$$$$$$$$$$$$$$")
        #print(group_value)
        #print("printing after %SOL% replace")
        #print(SOL_replace_str)
        #os.system(SOL_replace_str)
        os.system("echo q | gmx make_ndx -f newbox.gro")

        os.system("gmx grompp -f em.mdp -po mdout.mdp -c newbox.gro -p topol.top -o em.tpr -maxwarn 10")

        os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em -nt "+str(number_of_threads))
        # generate input files for trajcat
        # create input file for trjconv command
        file_gmx_trjconv_input = open("md_run_gmx_trjconv_input.txt","w+")
        file_gmx_trjconv_input.write("1\n0\nq\n")
        file_gmx_trjconv_input.close()
        os.system("gmx trjconv -s em.tpr -f em.gro -o em_em.xtc -pbc mol -ur compact -center < md_run_gmx_trjconv_input.txt")

        # Hotspot MD RUN ends here ----
        # os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
        # os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
        # os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
        # os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
        # os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
        # os.system("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
    return JsonResponse({'success': True})


#Substrate Parameterization
class Complex_Simulations(APIView):
    print('inside class Complex_Simulations(APIView):')
    def get(self,request):
        pass


    def post(self,request):
        string_data = " SOL "
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        user_id = commandDetails_result.user_id
        group_project_name = get_group_project_name(str(project_id))

        print("user_id is ",user_id)
        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
        # ligand_name = QzwProjectEssentials_res.command_key
        # print "+++++++++++++++ligand name is++++++++++++"
        # print ligand_name


        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+"/"+project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + '/CatMec/MD_Simulation/')
        print(os.system("pwd"))
        print(os.getcwd())
        print("=========== title is ==============")
        print(commandDetails_result.command_title)
        if commandDetails_result.command_title == "GromacsGenion":
            group_value = sol_group_option()
            ndx_file = "index.ndx"
            print(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/')
            dir_value = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/'
            os.system("rm "+dir_value+"/index.ndx")
            primary_command_runnable = re.sub('%SOL_value%',group_value,
                                              primary_command_runnable)
        if commandDetails_result.command_title == "md_run":
            returned_preparation_value = md_simulation_preparation(inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title,commandDetails_result.user_id)
            # print config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/'
            # dir_value = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/'
            # os.system("rm "+dir_value+"/index.ndx")
            # os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
            # os.system("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
            # os.system("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")
            # os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")
            # group_value = sol_group_option()
            # SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
            # SOL_replace_str = SOL_replace_backup
            # SOL_replace_str = SOL_replace_str.replace('%SOL_value%', group_value)
            # print("printing group value in MD$$$$$$$$$$$$$$$$$$")
            # print(group_value)
            # print("printing after %SOL% replace")
            # print(SOL_replace_str)
            # os.system(SOL_replace_str)
            # os.system("echo q | gmx make_ndx -f solve_ions.gro")
            # os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
            # os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")
            # os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
            # os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
            # os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
            # os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
            # os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
            # os.system(
            #     "gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
            # primary_command_runnable = re.sub('%SOL_value%',group_value,
            #                                   primary_command_runnable)

        if commandDetails_result.command_title == "Parameterize":
            print(config.PATH_CONFIG[
                      'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/')
            dir_value = config.PATH_CONFIG[
                            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/'
            # os.system("rm "+dir_value+"/NEWPDB.PDB")

        print(primary_command_runnable)

        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)

        command_title_folder = commandDetails_result.command_title

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)
        if process_return.returncode == 0:
            print("inside success")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("inside error")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#processing web crawler
class Literature_Research(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/')
        print(os.system("pwd"))
        # search keyword
        search_keyword = primary_command_runnable
        # convert keyword to URL encoded
        encoded_search_keyword = re.sub(" ", "%20", search_keyword)
        #
        start_offset = '?qs=' + encoded_search_keyword + '&show=100&sortBy=relevance&offset=0'
        start_page = '?qs=' + encoded_search_keyword + '&show=100&sortBy=relevance&offset='
        # result_crawlerdata_save = get_initial_crawler_data(start_offset,start_page,search_keyword)
        result_crawlerdata_save = get_crawler_data_gs(search_keyword,encoded_search_keyword)
        # paralleling functions

        get_initial_crawler_data(start_offset,start_page,search_keyword)
        get_crawler_data_pmd(search_keyword,encoded_search_keyword)
        get_crawler_data_gs(search_keyword,encoded_search_keyword)
        if result_crawlerdata_save == True:
            print("inside success")
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':result_crawlerdata_save,'process_returncode':result_crawlerdata_save})
        if result_crawlerdata_save == False:
            print("inside error")
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':result_crawlerdata_save,'process_returncode':result_crawlerdata_save})


class MakeSubstitution(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)


        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+"/"+project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        #primary_command_runnable = re.sub('%input_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        #primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['shared_folder_path']+'Project/Project1/'+commandDetails_result.command_tool+'/'+config.PATH_CONFIG['distance_python_file'],primary_command_runnable)
        #primary_command_runnable = re.sub('%output_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/')
        print(os.system("pwd"))
        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)
        if process_return.returncode == 0:
            print("inside success")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            # moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
            # moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            # move_outputFiles(moveFile_source, moveFile_destination)
            # if commandDetails_result.command_title == 'Solvate':
            #     topolfile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/GmxtoPdb/outputFiles/topol.top'
            #     topolfile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            #     move_topolfile_(topolfile_source,topolfile_destination)
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            #move_files_(inp_command_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print("inside error")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + group_project_name+"/"+project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
            # moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            # move_outputFiles(moveFile_source, moveFile_destination)
            #move_files_(inp_command_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})



#normalmode analysis
class NMA(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        group_project_name = get_group_project_name(str(project_id))

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        primary_command_runnable = re.sub("%tconcoord_python_filepath%",config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+  project_name + '/' + commandDetails_result.command_tool + '/Tconcoord.py',primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/tcc/',primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/input3.cpf', primary_command_runnable)
        primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)

        print("runnable command is ")
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool +'/')
        print("working directory is")
        print(os.system("pwd"))
        process_return = execute_command(primary_command_runnable, inp_command_id, user_email_string, project_name,
                                         project_id, commandDetails_result.command_tool,
                                         commandDetails_result.command_title)
        process_return.wait()
        shared_folder_path = config.PATH_CONFIG['shared_folder_path']
        command_title_folder = commandDetails_result.command_title

        out, err = process_return.communicate()
        process_return.wait()
        print("process return code is ")
        print(process_return.returncode)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


@csrf_exempt
def modeller_catmec_slurm_preparation(project_id,user_id,primary_command_runnable,file_path,job_name,windows_format_slurm_script,pre_slurm_script,slurm_script,server_value):
    group_project_name = get_group_project_name(str(project_id))
    print("inside modeller_catmec_slurm_preparation function")
    print("primary_command_runnable is ",primary_command_runnable)
    os.chdir(file_path)

    generate_modeller_catmec_slurm_script(file_path, server_value, job_name, pre_slurm_script, windows_format_slurm_script, primary_command_runnable)

    print('after generate_slurm_script ************************************************************************')
    print('before changing directory')
    print(os.getcwd())
    print('after changing directory')
    print(os.getcwd())
    print("Converting from windows to unix format")
    print("perl -p -e 's/\r$//' < "+windows_format_slurm_script+" > "+slurm_script)
    os.system("perl -p -e 's/\r$//' < "+windows_format_slurm_script+" > "+slurm_script)
    print('queuing **********************************************************************************')
    print("sbatch "+ file_path + "/" + slurm_script)
    cmd = "sbatch "+ file_path + "/" + slurm_script
    print("Submitting Job1 with command: %s" % cmd)
    status, jobnum = commands.getstatusoutput(cmd)
    print("job id is ", jobnum)
    print("status is ", status)
    print("job id is ", jobnum)
    print("status is ", status)
    print(jobnum.split())
    lenght_of_split = len(jobnum.split())
    index_value = lenght_of_split - 1
    print(jobnum.split()[index_value])
    job_id = jobnum.split()[index_value]
    # save job id
    job_id_key_name = "job_id"
    entry_time = datetime.now()
    try:
        print(
            "<<<<<<<<<<<<<<<<<<<<<<< in try of Homology Modelling JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                               project_id=project_id,
                                                                               entry_time=entry_time,
                                                                               job_id=job_id,
                                                                               job_status="1",
                                                                               job_title=job_name,
                                                                               job_details=job_name)
        QzwSlurmJobDetails_save_job_id.save()
    except db.OperationalError as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of Docking JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db.close_old_connections()
        QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                            project_id=project_id,
                                                            entry_time=entry_time,
                                                            job_id=job_id,
                                                            job_status="1",
                                                            job_title=job_name,
                                                            job_details=job_name)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")
    except Exception as e:
        print("<<<<<<<<<<<<<<<<<<<<<<< in except of Docking JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("exception is ",str(e))
        pass
        '''QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                               project_id=project_id,
                                                                               entry_time=entry_time,
                                                                               values=job_id,
                                                                               job_id=job_id)
        QzwSlurmJobDetails_save_job_id.save()
        print("saved")'''
    print('queued')
    return True


class Homology_Modelling(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        primary_command_runnable = re.sub("%build_profile_python_file_path%", config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)

        primary_command_runnable = re.sub('%compare_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%align_2d_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%evaluate_model_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%model_single_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        # editable_string = primary_command_runnable
        # editable_string = editable_string.split()
        # print("editable strign after split is")
        # target = editable_string[2]
        # print(target)
        # template = editable_string[3]
        # print(template)
        # residue_no = editable_string[4]
        # print(residue_no)
        # ending_model_no = editable_string[5]
        # print(ending_model_no)
        file_path = config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool
        os.chdir(file_path)

        dirName = os.getcwd()
        print("dirname")
        print(os.getcwd())

        print("runnable command is")
        print(primary_command_runnable)
        os.chdir(file_path)
        print("working directory after changing CHDIR")
        print(os.system("pwd"))

        initial_string = 'QZW_'
        module_name = 'Homology_Modelling'
        windows_modelling_script = 'homology_modelling_windows_format.sh'
        pre_modelling_script = 'pre_homology_modelling.sh'
        modelling_script = 'homology_modelling.sh'
        job_name = str(initial_string) + '_' + module_name
        server_value = 'allcpu'
        modeller_catmec_slurm_preparation(project_id, commandDetails_result.user_id, primary_command_runnable,
                                          file_path, job_name, windows_modelling_script,
                                          pre_modelling_script, modelling_script, server_value)
        primary_command_runnable = ""
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        print("execute command")
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print("printing status ofprocess")
        print(process_return.returncode)
        print("printing output of process")
        print(out)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< success try block homology modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< success except block homology modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< error try block homology modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< error except block homology modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


class Loop_Modelling(APIView):
    # inside loop modelling class
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        group_project_name = get_group_project_name(str(project_id))

        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

        primary_command_runnable = re.sub("%build_profile_python_file_path%", config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)

        primary_command_runnable = re.sub('%compare_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%align_2d_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%evaluate_model_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%model_single_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        # editable_string = primary_command_runnable
        # editable_string = editable_string.split()
        # print("editable strign after split is")
        # target = editable_string[2]
        # print(target)
        # template = editable_string[3]
        # print(template)
        # residue_no = editable_string[4]
        # print(residue_no)
        # ending_model_no = editable_string[5]
        # print(ending_model_no)
        file_path = config.PATH_CONFIG[
                        'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool
        os.chdir(file_path)

        dirName = os.getcwd()
        print("dirname")
        print(os.getcwd())

        print("runnable command is")
        print(primary_command_runnable)
        os.chdir(file_path)
        print("working directory after changing CHDIR")
        print(os.system("pwd"))
        # process_return = execute_command(primary_command_runnable)
        initial_string = 'QZW_'
        module_name = 'Loop_Modelling'
        windpws_modelling_script = 'loop_modelling_windows_format.sh'
        pre_modelling_script = 'pre_loop_modelling.sh'
        modelling_script = 'loop_modelling.sh'
        job_name = str(initial_string) + '_' + module_name
        server_value = 'allcpu'
        modeller_catmec_slurm_preparation(project_id, commandDetails_result.user_id, primary_command_runnable,
                                          file_path, job_name, windpws_modelling_script,
                                          pre_modelling_script, modelling_script, server_value)
        primary_command_runnable = ""
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        print("execute command")
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print("printing status ofprocess")
        print(process_return.returncode)
        print("printing output of process")
        print(out)

        if process_return.returncode == 0:
            print("success executing command")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< success try block loop modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< success except block loop modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print("error executing command!!")
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< error try block loop modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< error except block loop modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#ACTUAL WORKING AUTODOCK
#original service of autodock

# class autodock(APIView):
#     def get(self,request):
#         pass
#
#     def post(self,request):
#
#         #get command details from database
#         inp_command_id = request.POST.get("command_id")
#         commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
#         project_id = commandDetails_result.project_id
#         QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
#         project_name = QzwProjectDetails_res.project_name
#         primary_command_runnable = commandDetails_result.primary_command
#         if commandDetails_result.command_title == "GpftoGlg":
#             print "in GpftoGlg"
#             process_grid_file(commandDetails_result,QzwProjectDetails_res,request)
#         if commandDetails_result.command_title == "DpftoDlg":
#             print "in dpftodlg"
#             process_dock_file(commandDetails_result,QzwProjectDetails_res,request)
#
#         primary_command_runnable = re.sub("%prepare_ligand_python_file%", config.PATH_CONFIG['ligand_prepare_file_path'],primary_command_runnable)
#         primary_command_runnable = re.sub("%prepare_receptor_python_file%",config.PATH_CONFIG['receptor_file_path'],primary_command_runnable)
#         primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
#         primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
#         primary_command_runnable = re.sub('%angle_python_file%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/', primary_command_runnable)
#         primary_command_runnable = re.sub('%torsion_python_file%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' , primary_command_runnable)
#         primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
#         primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name +'/'+ commandDetails_result.command_tool + '/' ,primary_command_runnable)
#         #primary_command_runnable = re.sub('%input_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
#         #primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['shared_folder_path']+'Project/Project1/'+commandDetails_result.command_tool+'/'+config.PATH_CONFIG['distance_python_file'],primary_command_runnable)
#         #primary_command_runnable = re.sub('%output_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
#         print(primary_command_runnable)
#         #serializer = SnippetSerializer(commandDetails_result, many=True)
#         # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
#         process_return = execute_command(primary_command_runnable)
#         shared_folder_path = config.PATH_CONFIG['shared_folder_path']
#
#         command_title_folder = commandDetails_result.command_title
#         command_tool_title= commandDetails_result.command_tool
#
#         out, err = process_return.communicate()
#         if process_return.returncode == 0:
#             print "output of out is"
#             print out
#             fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
#             fileobj.write(out)
#             status_id = config.CONSTS['status_success']
#             moveFile_source = config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/outputFiles/'
#             moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
#             #move_outputFiles(moveFile_source,moveFile_destination)
#             update_command_status(inp_command_id,status_id)
#             #move_files_(inp_command_id)
#             return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
#         if process_return.returncode != 0:
#             fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
#             #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
#             fileobj.write(err)
#             status_id = config.CONSTS['status_error']
#             moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + commandDetails_result.command_title + '/outputFiles/'
#             moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
#             #move_outputFiles(moveFile_source, moveFile_destination)
#             update_command_status(inp_command_id,status_id)
#             #move_files_(inp_command_id)
#             return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#END OF ACTUALWORKING AUTODOCK

class CatMecandAutodock(APIView):
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        pre_command_title = commandDetails_result.command_title
        length_of_pre_command_title = len(pre_command_title.split('and')) - 1
        command_tool_title_string = pre_command_title.split('and')[length_of_pre_command_title]
        command_tool_title = pre_command_title.split('and')[length_of_pre_command_title-1]
        pre_command_tool = commandDetails_result.command_tool
        length_of_pre_command_tool = len(pre_command_tool.split('and')) - 1
        command_tool = pre_command_tool.split('and')[length_of_pre_command_tool - 1]
        user_id = commandDetails_result.user_id
        group_project_name = get_group_project_name(str(project_id))
        print("tool before")
        print(command_tool_title)
        print(command_tool)
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        key_name = 'enzyme_file'
        ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=key_name).latest("entry_time")
        enzyme_file_name = ProjectToolEssentials_res.key_values
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        print('\nbefore replacing primary_command_runnable')
        print(primary_command_runnable)
        #shared_scripts
        # primary_command_runnable = re.sub("pdb_to_pdbqt.py", config.PATH_CONFIG['shared_scripts'] +str(command_tool)+ "/pdb_to_pdbqt.py",primary_command_runnable)
        # primary_command_runnable = re.sub("%python_sh_path%",config.PATH_CONFIG['python_sh_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%prepare_ligand4_py_path%",config.PATH_CONFIG['prepare_ligand4_py_path'],primary_command_runnable)

        #rplace string / paths for normal mode analysis
        primary_command_runnable = re.sub("%tconcoord_python_filepath%", config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/Tconcoord_no_threading.py',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/tcc/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/input3.cpf',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG[
            'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title,
                                          primary_command_runnable)
        # if commandDetails_result.command_title == 'DockingandPdbtoPdbqt':
        #     file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool  +'/' + command_tool_title + '/'
        #     print("file path is ")
        #     print(file_path)
        #     new_shell_script_lines = ''
        #
        #     with open(file_path + 'pdb_to_pdbqt_win_frmt.sh', 'r') as source_file:
        #         print('inside opening ', file_path + 'pdb_to_pdbqt_win_frmt.sh')
        #         content = source_file.readlines()
        #         for line in content:
        #             if 'blast_1_cmd' in line:
        #                 new_shell_script_lines += (line.replace('PDB_TO_PDBQT_COMMAND', str(primary_command_runnable)))
        #             else:
        #                 new_shell_script_lines += line
        #     print("new_shell_script_lines is ")
        #     print(new_shell_script_lines)
        #     if os.path.exists(file_path + 'pdb_to_pdbqt_windows_frmt.sh'):
        #         os.remove(file_path + 'pdb_to_pdbqt_windows_frmt.sh')
        #     with open(file_path + 'pdb_to_pdbqt_windows_frmt.sh', 'w+')as new_bash_script:
        #         new_bash_script.write(new_shell_script_lines)
        #
        #     print(
        #         'after generate_shell script************************************************************************')
        #     print('before changing directory')
        #     print(os.getcwd())
        #     print('after changing directory')
        #     os.chdir(file_path)
        #     print(os.getcwd())
        #     print("Converting from windows to unix format")
        #     print("perl -p -e 's/\r$//' < pdb_to_pdbqt_windows_frmt.sh > pdb_to_pdbqt.sh")
        #     os.system("perl -p -e 's/\r$//' < pdb_to_pdbqt_windows_frmt.sh > pdb_to_pdbqt.sh")
        #     primary_command_runnable = 'sh pdb_to_pdbqt.sh'
        print(primary_command_runnable)
        print("\nworking directory before")
        print('\n',os.system("pwd"))
        '''check for command tool
            split command tool
           if command tool == NMA (normal mode analysis)
                change DIR to NMA
            else
                change DIR to Autodock
        '''
        str_command_tool_title = str(command_tool_title_string)
        print(type(str_command_tool_title))
        command_tool_title_split = str_command_tool_title.split('_')
        print("\nsplit is---------------------------------------------------------------------------------")
        print(type(command_tool_title_split))
        print(command_tool_title_split)
        # #append mmtsb path to command for NMA
        print('printing command tool title split length ++++++++++++++++++++++++++++++')
        print(len(command_tool_title_split))
        print(type(command_tool_title_split))
        print('len(command_tool_title.split)++++++++++++++++++++++++++++++++++++++++++++++')
        print(len(command_tool_title.split('_')))
        print(type(command_tool_title.split('_')))
        if not len(command_tool_title_split) <= 1:
            print('length is more than one @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            if (command_tool_title_split[1] == "nma"):
                print('command_tool_title_split[1] (one) is nma ',command_tool_title_split[1])
                primary_command_runnable = primary_command_runnable+" "+config.PATH_CONFIG['mmtsb_path']
                primary_command_runnable = primary_command_runnable + " " + enzyme_file_name
                print('primary_command_runnable ',primary_command_runnable)
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/')
            elif(command_tool_title_split[0] == "nma"):
                print('inside command_tool_title_split[0] (zero) is nma ',command_tool_title_split[0])
                print('printing path ',config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title +'/tconcoord/'+command_tool_title_split[2]+'/')
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' +  command_tool_title + '/tconcoord/'+command_tool_title_split[2]+'/')

            elif "tconcord_dlg" in str(command_tool_title_string):
                print('inside command_tool_title is tconcord_dlg ',command_tool_title)
                enzyme_file_key = 'autodock_nma_final_protein_conformation'
                ProjectToolEssentials_autodock_enzyme_file_name = ProjectToolEssentials.objects.all().filter(
                    project_id=project_id, key_name=enzyme_file_key).latest('entry_time')
                nma_enzyme_file = ProjectToolEssentials_autodock_enzyme_file_name.key_values
                nma_path = nma_enzyme_file[:-4]
                print(str(nma_path[:-4]))
                print('\nnma_path ****************************************')
                print(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/tconcoord/'+nma_path+'/')
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/tconcoord/'+nma_path+'/')
            else:
                print('inside else and lenght of split is more than 1')
                print(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool  +'/' + command_tool_title + '/')
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool  +'/' + command_tool_title + '/')
        else:
            if str_command_tool_title == "bundle":
                file_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool  +'/' + command_tool_title
                initial_string = 'QZW_'
                module_name = 'Docking'
                docking_script = 'docking.sh'
                pre_docking_script = 'pre_docking.sh'
                windows_docking_script = 'pre_docking_windows_format.sh'
                job_name = str(initial_string) + '_' + module_name
                # server_value = 'allcpu'
                server_value = 'qzyme2'

                enzyme_key = 'enzyme_file'
                ligand_key = 'ligand_file'

                ProjectToolEssentials_enzyme_res = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=enzyme_key).latest('entry_time')
                enzyme_file_name = ProjectToolEssentials_enzyme_res.key_values

                ProjectToolEssentials_substrate_res = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=ligand_key).latest('entry_time')
                autodock_substrate_file_name = ProjectToolEssentials_substrate_res.key_values

                enzyme_dlg_file_without_extension = enzyme_file_name[:-4]
                enzyme_dlg_file_name = enzyme_dlg_file_without_extension + '.dlg'

                primary_command_runnable = config.PATH_CONFIG[
                                                   'dlg_to_pdb_command'] + ' ' + enzyme_dlg_file_name + ' ALL ' + autodock_substrate_file_name

                modeller_catmec_slurm_preparation(project_id, commandDetails_result.user_id, primary_command_runnable,
                                                  file_path, job_name, windows_docking_script,
                                                  pre_docking_script, docking_script, server_value)
                primary_command_runnable = ""
            print('inside else')
            print(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + command_tool_title + '/')
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'CatMec' + '/' + command_tool_title + '/')
        print("\nworking directory after changing CHDIR")
        print(os.system("pwd"))


        print("\nexecute command before ")
        print(primary_command_runnable)



        process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, command_tool,command_tool_title)
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        # command_title_folder = command_tool_title_string
        # command_tool_title = commandDetails_result.command_tool
        print("\nprinting status ofprocess")
        print(process_return.returncode)
        print("\nprinting output of process")
        print(out)

        if process_return.returncode == 0:
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< in try autodock >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of Docking >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
        if process_return.returncode != 0:
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< in try autodock status error >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'CatMec' + '/' + command_tool_title + '/' +command_tool_title_string + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except autodock error >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + 'CatMec' + '/' + command_tool_title + '/' + command_tool_title_string + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})

        # before trying t solve lost connection issue
        # if process_return.returncode == 0:
        #     print "output of out is"
        #     print out
        #     fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
        #     fileobj.write(out)
        #     status_id = config.CONSTS['status_success']
        #     update_command_status(inp_command_id,status_id)
        #     return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        # if process_return.returncode != 0:
        #     fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
        #     fileobj.write(err)
        #     status_id = config.CONSTS['status_error']
        #     update_command_status(inp_command_id,status_id)
        #     return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

        #get command details from database
        # inp_command_id = request.POST.get("command_id")
        # commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        # project_id = commandDetails_result.project_id
        # QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        # project_name = QzwProjectDetails_res.project_name
        # primary_command_runnable = commandDetails_result.primary_command
        # if  commandDetails_result.command_title == "PdbtoPdbqt":
        #     print "in pdbtopdbqt"
        # if commandDetails_result.command_title == "GpftoGlg":
        #     print "in GpftoGlg"
        #     process__file(commandDetails_result,QzwProjectDetails_res,request)
        # if commandDetails_result.command_title == "DpftoDlg":
        #     print "in dpftodlg"
        #     process_dock_file(commandDetails_result,QzwProjectDetails_res,request)
        #
        # primary_command_runnable = re.sub("%prepare_ligand_python_file%", config.PATH_CONFIG['ligand_prepare_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%prepare_receptor_python_file%",config.PATH_CONFIG['receptor_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        # primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        # primary_command_runnable = re.sub('%angle_python_file%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/', primary_command_runnable)
        # primary_command_runnable = re.sub('%torsion_python_file%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' , primary_command_runnable)
        # primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        # primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name +'/'+ commandDetails_result.command_tool + '/' ,primary_command_runnable)
        # #primary_command_runnable = re.sub('%input_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        # #primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['shared_folder_path']+'Project/Project1/'+commandDetails_result.command_tool+'/'+config.PATH_CONFIG['distance_python_file'],primary_command_runnable)
        # #primary_command_runnable = re.sub('%output_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        # print(primary_command_runnable)
        # #serializer = SnippetSerializer(commandDetails_result, many=True)
        # # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        # process_return = execute_command(primary_command_runnable)
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']
        #
        # command_title_folder = commandDetails_result.command_title
        # command_tool_title= commandDetails_result.command_tool
        #
        # out, err = process_return.communicate()
        # if process_return.returncode == 0:
        #     print "output of out is"
        #     print out
        #     fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
        #     fileobj.write(out)
        #     status_id = config.CONSTS['status_success']
        #     moveFile_source = config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/outputFiles/'
        #     moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
        #     #move_outputFiles(moveFile_source,moveFile_destination)
        #     update_command_status(inp_command_id,status_id)
        #     #move_files_(inp_command_id)
        #     return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        # if process_return.returncode != 0:
        #     fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
        #     #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
        #     fileobj.write(err)
        #     status_id = config.CONSTS['status_error']
        #     moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + commandDetails_result.command_title + '/outputFiles/'
        #     moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
        #     #move_outputFiles(moveFile_source, moveFile_destination)
        #     update_command_status(inp_command_id,status_id)
        #     #move_files_(inp_command_id)
        #     return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


class CatMec(APIView):
    print('inside class CatMec')
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_result = QzwProjectDetails.objects.get(project_id=str(project_id))
        project_name = QzwProjectDetails_result.project_name
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        group_project_name = get_group_project_name(str(project_id))
        slurm_job_ids = []
        if command_tool_title == "Replace_Charge":
            print(command_tool_title)
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name

            primary_command_runnable = re.sub("%input_folder_name%", config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/Ligand_Parametrization/')
            print(os.system("pwd"))
            print(os.getcwd())
            print("=========== title is ==============")
            print(commandDetails_result.command_title)
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, command_tool,command_tool_title)
            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + group_project_name+"/"+project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id,user_email_string,project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "process_pdb_with_babel":
            print('inside process_pdb_with_babel section')
            print(command_tool_title)
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            print("before command update")
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            print("after command update")
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + config.PATH_CONFIG['ligand_parametrization_path'] + '/')
            print('after change directory is ',os.getcwd())
            print("=========== title is ==============")
            print(commandDetails_result.command_title)

            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, command_tool,command_tool_title)
            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print("<<<<<<<<<<<<<<<<<<<<<<< error try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "Ligand_Parametrization":
            '''print('exec(open(/usr/share/Modules/init/python.py).read())')
            try:
                # module accessing
                exec(open('/usr/share/Modules/init/python.py').read())
                print('module(unload mgltools)')
                module('unload mgltools')
            except Exception as e:
                print("inside exception of unload mgltools in LP ",str(e))'''
            print('command_tool_title is ',command_tool_title)
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name

            primary_command_runnable = re.sub("%input_folder_name%", config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            file_path = config.PATH_CONFIG[
                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/'
            os.chdir(file_path)
            print(os.system("pwd"))
            print(os.getcwd())
            print("=========== title is ==============")
            print(commandDetails_result.command_title)

            if commandDetails_result.command_title == "Parameterize":
                print(config.PATH_CONFIG[
                          'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/')
                dir_value = config.PATH_CONFIG[
                                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/'
                # os.system("rm "+dir_value+"/NEWPDB.PDB")

            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)


            print('primary_command_runnable.split()[1]',primary_command_runnable.split()[1])
            if primary_command_runnable.split()[1] == "pre_process_parameterize.py":
                ##########################################
                initial_string = 'QZW'
                module_name = 'Ligand_Parametrization'
                windows_parametrization_script = 'parametrization_windows_format.sh'
                pre_parametrization_script = 'pre_parametrization.sh'
                parametrization_script = 'parametrization.sh'
                job_name = str(initial_string) + '_' + module_name
                server_value = 'allcpu'

                modeller_catmec_slurm_preparation(project_id, commandDetails_result.user_id, primary_command_runnable,
                                                  file_path, job_name, windows_parametrization_script,
                                                  pre_parametrization_script, parametrization_script, server_value)
                primary_command_runnable = ""
                ##########################################

            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                '''
                try:
                    # module accessing
                    exec (open('/usr/share/Modules/init/python.py').read())
                    print('module(load mgltools)')
                    module('load mgltools')
                except Exception as e:
                    print("inside exception of load mgltools in LP ", str(e))'''
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print("<<<<<<<<<<<<<<<<<<<<<<< error try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                '''
                try:
                    # module accessing
                    exec (open('/usr/share/Modules/init/python.py').read())
                    print('module(load mgltools)')
                    module('load mgltools')
                except Exception as e:
                    print("inside exception of load mgltools in LP ", str(e))'''
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "get_make_complex_parameter_details" or command_tool_title == "make_complex_params" or command_tool_title == "md_run":
            print('command_tool_title ----------------------\n')
            print(command_tool_title)
            user_id = commandDetails_result.user_id
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            group_project_name = get_group_project_name(str(project_id))
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(ppartial_charge_selection_nameroject_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name
            simulation_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + '/CatMec/MD_Simulation/'
            os.chdir(simulation_path)
            print (os.getcwd())

            if commandDetails_result.command_title == "md_run":
                md_simulation_path = '/CatMec/MD_Simulation/'
                print('md simulation path in md_run is')
                print(simulation_path)
                md_simulation_preparation(inp_command_id,project_id, project_name, commandDetails_result.command_tool,
                                          commandDetails_result.command_title,user_id,md_simulation_path)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block get_make_complex_parameter_details or make_complex_params or md_run >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block get_make_complex_parameter_details or make_complex_params or md_run  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True})
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)

            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block get_make_complex_parameter_details or make_complex_params or md_run >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block get_make_complex_parameter_details or make_complex_params or md_run  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error try block get_make_complex_parameter_details or make_complex_params or md_run >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block get_make_complex_parameter_details or make_complex_params or md_run  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "umbrella_sampling_pull_simulation":
            print('command_tool_title ----------------------\n')
            print(command_tool_title)
            user_id = commandDetails_result.user_id
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            group_project_name = get_group_project_name(str(project_id))
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(ppartial_charge_selection_nameroject_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name
            simulation_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG['umbrella_sampling_path']

            ############################################################################################################
            ##################################US SIMULATION STEP 1 START################################################
            ############################################################################################################
            print('after generate_slurm_script ************************************************************************')
            print('before changing directory')
            print(os.getcwd())
            print('after changing directory')
            os.chdir(simulation_path)
            print (os.getcwd())
            print("Converting from windows to unix format")
            print("perl -p -e 's/\r$//' < pull_windows.mdp > pull.mdp")
            os.system("perl -p -e 's/\r$//' < pull_windows.mdp > pull.mdp")
            print("perl -p -e 's/\r$//' < pre_simulation_windows.sh > simulation.sh")
            os.system("perl -p -e 's/\r$//' < pre_simulation_windows.sh > simulation.sh")
            print('queuing **********************************************************************************')
            cmd = "sbatch "+ simulation_path + "/" + "simulation.sh"
            print("Submitting Job1 with command: %s" % cmd)
            status, jobnum = commands.getstatusoutput(cmd)
            print("job id is ", jobnum)
            print("status is ", status)
            print("job id is ", jobnum)
            print("status is ", status)
            print(jobnum.split())
            lenght_of_split = len(jobnum.split())
            index_value = lenght_of_split - 1
            print(jobnum.split()[index_value])
            job_id = jobnum.split()[index_value]
            initial_string = 'QZW'
            module_name = config.PATH_CONFIG['umbrella_sampling_step_one_title']
            job_name = str(initial_string) + '_' + module_name
            job_detail_string = module_name
            # save job id
            job_id_key_name = "job_id"
            entry_time = datetime.now()
            try:
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling pull SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")
            except Exception as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling pull SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print("exception is ",str(e))
                pass
            ############################################################################################################
            ##################################US SIMULATION STEP 1 END##################################################
            ############################################################################################################
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)

            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
            # process_return = execute_umbrella_sampling_command(job_id,primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title,job_id)
            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block UMBRELLA SAMPLING STEP ONE >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block UMBRELLA SAMPLING STEP ONE  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error try block UMBRELLA SAMPLING STEP ONE >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block UMBRELLA SAMPLING STEP ONE  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "umbrella_sampling_production_simulation":
            print('command_tool_title ----------------------\n')
            print(command_tool_title)
            user_id = commandDetails_result.user_id
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            group_project_name = get_group_project_name(str(project_id))
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(ppartial_charge_selection_nameroject_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name
            simulation_path = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG['umbrella_sampling_path']

            ############################################################################################################
            ##################################US SIMULATION STEP 4 START################################################
            ############################################################################################################
            print('after generate_slurm_script ************************************************************************')
            print('before changing directory')
            print(os.getcwd())
            print('after changing directory')
            os.chdir(simulation_path)
            print (os.getcwd())
            print("Converting from windows to unix format")
            print("perl -p -e 's/\r$//' < production_windows.mdp > production.mdp")
            os.system("perl -p -e 's/\r$//' < production_windows.mdp > production.mdp")
            print("perl -p -e 's/\r$//' < pre_extract_pdb_windows.sh > extract_pdb.sh")
            os.system("perl -p -e 's/\r$//' < pre_extract_pdb_windows.sh > extract_pdb.sh")
            # print("perl -p -e 's/\r$//' < pre_production_simulation_windows.sh > production_simulation.sh")
            # os.system("perl -p -e 's/\r$//' < pre_production_simulation_windows.sh > production_simulation.sh")
            print('queuing **********************************************************************************')
            cmd = "sbatch "+ simulation_path + "/" + "extract_pdb.sh"
            print("Submitting Job1 with command: %s" % cmd)
            status, jobnum = commands.getstatusoutput(cmd)
            print("job id is ", jobnum)
            print("status is ", status)
            print("job id is ", jobnum)
            print("status is ", status)
            print(jobnum.split())
            lenght_of_split = len(jobnum.split())
            index_value = lenght_of_split - 1
            print(jobnum.split()[index_value])
            job_id = jobnum.split()[index_value]
            dependant_job_id = int(job_id)
            slurm_job_ids.append(dependant_job_id)
            initial_string = 'QZW'
            module_name = config.PATH_CONFIG['umbrella_sampling_step_four_title']
            job_name = str(initial_string) + '_' + module_name
            job_detail_string = module_name
            # save job id
            job_id_key_name = "job_id"
            entry_time = datetime.now()
            try:
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling production SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                    project_id=project_id,
                                                                    entry_time=entry_time,
                                                                    job_id=job_id,
                                                                    job_status="1",
                                                                    job_title=job_name,
                                                                    job_details=job_detail_string)
                QzwSlurmJobDetails_save_job_id.save()
                print("saved")
            except Exception as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling production SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print("exception is ",str(e))
                pass
            sim_val = retrieve_project_tool_essentials_values(project_id,'frames_selected_value')
            for frm_val in eval(sim_val):
                print("perl -p -e 's/\r$//' < pre_production_simulation_"+str(frm_val)+"_windows.sh > production_simulation_"+str(frm_val)+".sh")
                os.system("perl -p -e 's/\r$//' < pre_production_simulation_"+str(frm_val)+"_windows.sh > production_simulation_"+str(frm_val)+".sh")
                cmd = "sbatch --dependency=afterok:" +str(dependant_job_id)+ " " + simulation_path + "production_simulation_"+str(frm_val)+".sh"
                print("Submitting Job1 with command: %s" % cmd)
                status, jobnum = commands.getstatusoutput(cmd)
                print("job id is ", jobnum)
                print("status is ", status)
                print("job id is ", jobnum)
                print("status is ", status)
                print(jobnum.split())
                lenght_of_split = len(jobnum.split())
                index_value = lenght_of_split - 1
                print(jobnum.split()[index_value])
                job_id = jobnum.split()[index_value]
                slurm_job_ids.append(dependant_job_id)
                initial_string = 'QZW'
                module_name = config.PATH_CONFIG['umbrella_sampling_step_four_title']
                job_name = str(initial_string) + '_' + module_name
                job_detail_string = module_name
                # save job id
                job_id_key_name = "job_id"
                entry_time = datetime.now()
                try:
                    QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                        project_id=project_id,
                                                                        entry_time=entry_time,
                                                                        job_id=job_id,
                                                                        job_status="1",
                                                                        job_title=job_name,
                                                                        job_details=job_detail_string)
                    QzwSlurmJobDetails_save_job_id.save()
                except db.OperationalError as e:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling production SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    QzwSlurmJobDetails_save_job_id = QzwSlurmJobDetails(user_id=user_id,
                                                                        project_id=project_id,
                                                                        entry_time=entry_time,
                                                                        job_id=job_id,
                                                                        job_status="1",
                                                                        job_title=job_name,
                                                                        job_details=job_detail_string)
                    QzwSlurmJobDetails_save_job_id.save()
                    print("saved")
                except Exception as e:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in except of Umbrella Sampling production SLURM JOB SCHEDULING >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print("exception is ",str(e))
                    pass
            ############################################################################################################
            ##################################US SIMULATION STEP 4 END##################################################
            ############################################################################################################
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title,slurm_job_ids)
            # process_return = execute_umbrella_sampling_command(primary_command_runnable, inp_command_id,user_email_string,project_name,project_id, commandDetails_result.command_tool,commandDetails_result.command_title,slurm_job_ids)
            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print("process return code is ")
            print(process_return.returncode)
            if process_return.returncode == 0:
                print("inside success")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block UMBRELLA SAMPLING STEP FOUR >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block UMBRELLA SAMPLING STEP FOUR  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print("inside error")
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error try block UMBRELLA SAMPLING STEP FOUR >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block UMBRELLA SAMPLING STEP FOUR  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})


        elif command_tool_title == "MD_Simulation":
            print(command_tool_title)
        elif command_tool_title == "Docking":
            print(command_tool_title)
            print("tool before")
            print(command_tool_title)
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            key_name = 'enzyme_file'
            ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                   key_name=key_name).latest("entry_time")
            enzyme_file_name = ProjectToolEssentials_res.key_values
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            #shared_scripts
            primary_command_runnable = re.sub("pdb_to_pdbqt.py", config.PATH_CONFIG['shared_scripts'] +str(command_tool)+ +str(command_tool_title)+ "/pdb_to_pdbqt.py",primary_command_runnable)
            primary_command_runnable = re.sub("%python_sh_path%",config.PATH_CONFIG['python_sh_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%prepare_ligand4_py_path%",config.PATH_CONFIG['prepare_ligand4_py_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%add_python_file_path%",config.PATH_CONFIG['add_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%make_gpf_dpf_python_file_path%",config.PATH_CONFIG['make_gpf_dpf_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%grid_dock_map_python_file_path%",config.PATH_CONFIG['grid_dock_map_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%multiple_distance_python_file_path%",config.PATH_CONFIG['multiple_distance_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%multiple_angle_python_file_path%",config.PATH_CONFIG['multiple_angle_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%multiple_torsion_python_file_path%",config.PATH_CONFIG['multiple_torsion_python_file_path'],primary_command_runnable)
            primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                              primary_command_runnable)

            #rplace string / paths for normal mode analysis
            primary_command_runnable = re.sub("%tconcoord_python_filepath%", config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/Tconcoord_no_threading.py',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/tcc/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/input3.cpf',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/',
                                              primary_command_runnable)
            #append mmtsb path to command for NMA
            primary_command_runnable = primary_command_runnable+" "+config.PATH_CONFIG['mmtsb_path']
            primary_command_runnable = primary_command_runnable+" "+enzyme_file_name
            print(primary_command_runnable)
            print("working directory before")
            print(os.system("pwd"))
            '''check for command tool
                split command tool
               if command tool == NMA (normal mode analysis)
                    change DIR to NMA
                else
                    change DIR to Autodock
            '''
            str_command_tool_title = str(command_tool_title)
            print(type(str_command_tool_title))
            command_tool_title_split = str_command_tool_title.split('_')
            print("split is----------------------------")
            print(type(command_tool_title_split))
            print(command_tool_title_split)
            if(command_tool_title_split[0] == "nma"):
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+command_tool_title_split[2]+'/')
            else:
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/'+ commandDetails_result.command_title + '/')
            print("working directory after changing CHDIR")
            print(os.system("pwd"))
            # process PDB file format with PDBFIXER(MMTSB)
            if command_tool_title == "PdbtoPdbqt":
                #split primary_command_runnable and get PDB file as input to PDBFIXER
                primary_command_runnable_split = primary_command_runnable.split()
                os.system(config.PATH_CONFIG['mmtsb_path']+"/convpdb.pl "+primary_command_runnable_split[2]+" "+"-out generic > fixer_test.pdb")
                os.system("mv fixer_test.pdb "+primary_command_runnable_split[2])
            #process_return = execute_command(primary_command_runnable)
            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )
            print("execute command")
            out, err = process_return.communicate()
            process_return.wait()
            # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

            command_title_folder = commandDetails_result.command_title
            command_tool_title= commandDetails_result.command_tool
            print("printing status ofprocess")
            print(process_return.returncode)
            print("printing output of process")
            print(out)

            if process_return.returncode == 0:
                print("output of out is")
                print(out)
                fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
                fileobj.write(out)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success try block Catmec docking condition   >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< success except block Catmec docking condition   >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
            if process_return.returncode != 0:
                fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
                fileobj.write(err)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error try block Catmec docking condition >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< error except block Catmec docking condition  >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                #move_files_(inp_command_id)
                return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})



class Designer(APIView):
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        user_id = commandDetails_result.user_id
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        group_project_name = get_group_project_name(str(project_id))
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' )
        print(os.system("pwd"))
        primary_command_runnable = commandDetails_result.primary_command
        primary_command_runnable_split = primary_command_runnable.split(" ")
        if primary_command_runnable.strip() == "python run_md.py":
            #execute MD simulations
            primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
            md_simulation_preparation(inp_command_id,project_id, project_name, command_tool = commandDetails_result.command_tool,
                                      command_title = commandDetails_result.command_title)

        elif command_tool_title == "Designer_Mutations":
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            # execute Designer Mutations
            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                # Execute MAKE COMPLEX
                '''
                ooo        ooooo       .o.       oooo    oooo oooooooooooo        .oooooo.     .oooooo.   ooo        ooooo ooooooooo.   ooooo        oooooooooooo ooooooo  ooooo 
                `88.       .888'      .888.      `888   .8P'  `888'     `8       d8P'  `Y8b   d8P'  `Y8b  `88.       .888' `888   `Y88. `888'        `888'     `8  `8888    d8'  
                 888b     d'888      .8"888.      888  d8'     888              888          888      888  888b     d'888   888   .d88'  888          888            Y888..8P    
                 8 Y88. .P  888     .8' `888.     88888[       888oooo8         888          888      888  8 Y88. .P  888   888ooo88P'   888          888oooo8        `8888'     
                 8  `888'   888    .88ooo8888.    888`88b.     888    "         888          888      888  8  `888'   888   888          888          888    "       .8PY888.    
                 8    Y     888   .8'     `888.   888  `88b.   888       o      `88b    ooo  `88b    d88'  8    Y     888   888          888       o  888       o   d8'  `888b   
                o8o        o888o o88o     o8888o o888o  o888o o888ooooood8       `Y8bood8P'   `Y8bood8P'  o8o        o888o o888o        o888ooooood8 o888ooooood8 o888o  o88888o 
                '''
                queue_make_complex_params(request, project_id, user_id, command_tool_title, command_tool, project_name)
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< in success try mutations after make complex, md run and MMPBSA   >>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< in success except mutations after make complex, md run and MMPBSA >>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                try:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< in error try mutations after make complex, md run and MMPBSA >>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

                except db.OperationalError as e:
                    print(
                        "<<<<<<<<<<<<<<<<<<<<<<< in error except mutations after make complex, md run and MMPBSA  >>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})

        elif primary_command_runnable_split[1] == "make_complex.py":
            #Make Complex Execution
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/'+command_tool_title)

            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )

            print("execute command")
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                print("output of out is")
                print(out)
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        else:
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )

            print("execute command")
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                print("output of out is")
                print(out)
                try:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in else success try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

                except db.OperationalError as e:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in else success except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                try:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in else error try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

                except db.OperationalError as e:
                    print("<<<<<<<<<<<<<<<<<<<<<<< in else error except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})


# Hotspot module
class Hotspot(APIView):
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        user_id = commandDetails_result.user_id
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        group_project_name = get_group_project_name(str(project_id))
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/' )
        print(os.system("pwd"))
        # fetch ligand names from DB
        ligands_key_name = 'substrate_input'
        ProjectToolEssentials_ligand_name_res = ProjectToolEssentials.objects.all().filter(
            project_id=project_id,
            key_name=ligands_key_name).latest(
            'entry_time')
        ligand_names = ProjectToolEssentials_ligand_name_res.key_values
        ligand_file_data = ast.literal_eval(ligand_names)
        ligand_names_list = []
        for key, value in ligand_file_data.items():
            # value.split('_')[0] is ligand name
            ligand_names_list.append(value.split('_')[0])

        # ---------   remove ligand from protien file   ----------

        # loop thru PDB files in dir
        ligand_dir_counter = 0
        for dir_files in listdir(config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool):
            if dir_files.endswith(".pdb"):  # applying .pdb filter
                os.system("mkdir " + dir_files[:-4])
                #create ligand files for each frame(PDB)
                for ligand_l in ligand_names_list:
                    os.system("grep '"+str(ligand_l)+"'"+" "+config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/'+ dir_files+" > "+config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/'+dir_files[:-4]+"/"+ligand_l+".pdb")

                protien_without_ligand_lines = ""
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/'+ dir_files, "r") as variant_pdb_file:
                    variant_pdb_file_lines = variant_pdb_file.readlines()
                    for variant_pdb_file_line in variant_pdb_file_lines:
                        if not any(ligand_l in variant_pdb_file_line for ligand_l in ligand_names_list):
                            protien_without_ligand_lines += variant_pdb_file_line


                # renaming protien file - backup protien file
                os.rename(config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/'+dir_files,
                          config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/' + "/backup_" + dir_files[:-4] + ".txt")

                # write to protien file (without ligands)
                with open(config.PATH_CONFIG[
                              'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/' +dir_files, "w+") as variant_pdb_newfile:
                    variant_pdb_newfile.write(protien_without_ligand_lines)
            ligand_dir_counter += 1

        primary_command_runnable = commandDetails_result.primary_command

        # execute Hotspot Mutations
        # get python scripts
        shutil.copyfile(
            config.PATH_CONFIG['shared_scripts'] + commandDetails_result.command_tool + '/create_mutation.py',
            config.PATH_CONFIG[
                'local_shared_folder_path'] + group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/create_mutation.py')
        shutil.copyfile(
            config.PATH_CONFIG['shared_scripts'] + commandDetails_result.command_tool + '/pymol_mutate.py',
            config.PATH_CONFIG[
                'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + commandDetails_result.command_tool + '/pymol_mutate.py')
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        out, err = process_return.communicate()
        process_return.wait()
        if process_return.returncode == 0:
            # Execute MAKE COMPLEX
            '''
            ooo        ooooo       .o.       oooo    oooo oooooooooooo        .oooooo.     .oooooo.   ooo        ooooo ooooooooo.   ooooo        oooooooooooo ooooooo  ooooo 
            `88.       .888'      .888.      `888   .8P'  `888'     `8       d8P'  `Y8b   d8P'  `Y8b  `88.       .888' `888   `Y88. `888'        `888'     `8  `8888    d8'  
             888b     d'888      .8"888.      888  d8'     888              888          888      888  888b     d'888   888   .d88'  888          888            Y888..8P    
             8 Y88. .P  888     .8' `888.     88888[       888oooo8         888          888      888  8 Y88. .P  888   888ooo88P'   888          888oooo8        `8888'     
             8  `888'   888    .88ooo8888.    888`88b.     888    "         888          888      888  8  `888'   888   888          888          888    "       .8PY888.    
             8    Y     888   .8'     `888.   888  `88b.   888       o      `88b    ooo  `88b    d88'  8    Y     888   888          888       o  888       o   d8'  `888b   
            o8o        o888o o88o     o8888o o888o  o888o o888ooooood8       `Y8bood8P'   `Y8bood8P'  o8o        o888o o888o        o888ooooood8 o888ooooood8 o888o  o88888o 
            '''
            hotspot_queue_make_complex_params(request, project_id, user_id, command_tool_title, command_tool, project_name)


            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< in try mutations success >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)
            return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
        if process_return.returncode != 0:
            try:
                print("<<<<<<<<<<<<<<<<<<<<<<< in try mutations error >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            except db.OperationalError as e:
                print("<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id, user_email_string, project_name, project_id, commandDetails_result.command_tool,commandDetails_result.command_title)

            return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})



#queue MAKE COMPLEX params command to DB
def queue_make_complex_params(request,project_id, user_id,  command_tool_title, command_tool, project_name):
    group_project_name = get_group_project_name(str(project_id))
    #get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "designer_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    designer_mutations_file = ProjectToolEssentials_mutations_file.key_values

    # open mutated text file and loop thru to prepare files for make_complex.py
    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              +group_project_name+"/"+ project_name + '/' + command_tool + '/'+designer_mutations_file, 'r'
              ) as fp_mutated_list:
        mutated_list_lines = fp_mutated_list.readlines()
        variant_index_count = 0
        for line in mutated_list_lines:
            # process  PDB file to get amino acids as python dict
            ''' PDB PARSER
                           ATOM / HETAATM  STRING line[0:6]
                           INDEX           STRING line[6:11]
                           ATOM TYPE       STRING line[12:16]
                           AMINO ACID      STRING line[17:20]
                           CHAIN ID        STRING line[21:22]
                           RESIDUE NO      STRING line[22:26]
                           X CO-ORDINATE   STRING line[30:38]
                           Y CO-ORDINATE   STRING line[38:46]
                           Z CO-ORDINATE   STRING line[46:54]
                           '''
            aminoacids_list = []
            # prepare a text file of all amino acids with residue number and serial number from PDB file
            with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                      +group_project_name+"/"+ project_name + '/' + command_tool +'/'+line.strip()+ '/variant_'+str(variant_index_count)+'.pdb', 'r'
                      ) as fp_variant_pdb:
                variant_pdb_lines = fp_variant_pdb.readlines()
                for line_pdb in variant_pdb_lines:
                    if line_pdb[0:6].strip() == "ATOM" or line_pdb[0:6].strip() == "HETAATM":
                        if line_pdb[22:26].strip() + "_" + line_pdb[17:20].strip() not in aminoacids_list:
                            # append all amino acids to list
                            aminoacids_list.append(line_pdb[22:26].strip() + "_" + line_pdb[17:20].strip())

            designer_protonation_matrix = ""
            protonation_ac_list = ["ASP", "GLU", "HIS", "LYS"]
            #copy protonation files from CatMec module to Designer
            for atoms_name in protonation_ac_list:
                try:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/'+atoms_name+"_protonate.txt",config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/' + command_tool +'/'+line.strip()+"/"+atoms_name+"_protonate.txt")
                except IOError as e:
                    pass

            for atoms_name in protonation_ac_list:
                try:
                    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/' + command_tool + '/' +line.strip()+"/"+ atoms_name + '_protonate.txt', 'r'
                          ) as file_pointer:
                        lines_protonation_atoms = file_pointer.readlines()
                        for line_in_protonate_atoms in lines_protonation_atoms:
                            if line_in_protonate_atoms.split()[1] + "_" + line_in_protonate_atoms.split()[0] not in aminoacids_list:
                                pass
                            else:
                                designer_protonation_matrix += line_in_protonate_atoms
                except IOError as e:
                    pass



            # remove protonations input and matrix files if exsist
            try:
                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/' + command_tool +"/"+line.strip()+'/designer_final_matrix_pdb_pqr_protonate.txt')
                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/' + command_tool +"/"+ line.strip()+'/protonate_input.txt')
            except:
                pass

            # prepare final matrix file of protonation values
            try:
                outFile = open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                               +group_project_name+"/"+ project_name + '/' + command_tool +"/"+ line.strip() +'/designer_final_matrix_pdb_pqr_protonate.txt',
                               'w+')
                outFile.write(designer_protonation_matrix)
                outFile.close()
            except IOError as (errno, strerror):
                print("I/O error({0}): {1}".format(errno, strerror))

            # prepare final protonation input text file
            with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                      +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + '/protonate_input.txt', 'w+'
                      ) as input_file_ptr:
                with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt', 'r'
                          ) as matrix_file_ptr:
                    matrix_file_lines = matrix_file_ptr.readlines()
                    for matrix_file_line in matrix_file_lines:
                        input_file_ptr.write(matrix_file_line.split()[-1] + '\n')

            #get python script for make_compex execution
            shutil.copyfile(config.PATH_CONFIG['shared_scripts'] +'CatMec/MD_Simulation/' +"make_complex.py",
                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" +"make_complex.py")

            #get make_complex parameters from DB
            make_complex_params_keyname = "make_complex_parameters"
            try:
                print("in make_complex_parameters query try first DB operation")
                ProjectToolEssentials_make_complex_params = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=make_complex_params_keyname).latest(
                        'entry_time')
                make_complex_params = ProjectToolEssentials_make_complex_params.key_values
            except db.OperationalError as e:
                print("in make_complex_parameters query except first DB operation")
                db.close_old_connections()
                ProjectToolEssentials_make_complex_params = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=make_complex_params_keyname).latest(
                        'entry_time')
                make_complex_params = ProjectToolEssentials_make_complex_params.key_values


            variant_protien_file = 'variant_'+str(variant_index_count)+'.pdb'
            # replace protien file in make_complex_params
            make_complex_params_replaced = re.sub(r'(\w+)(\.pdb)', variant_protien_file, make_complex_params)

            #copy ligand .GRO files and .ITP files from CatMec module
            ligands_key_name = 'substrate_input'
            ProjectToolEssentials_ligand_name_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                               key_name=ligands_key_name).latest(
                'entry_time')
            ligand_names = ProjectToolEssentials_ligand_name_res.key_values
            ligand_file_data = ast.literal_eval(ligand_names)
            for key, value in ligand_file_data.items():
                #value.split('_')[0]
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                +group_project_name+"/"+ project_name + '/CatMec/Ligand_Parametrization/' + str(value.split('_')[0]) + ".gro",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + str(value.split('_')[0]) + ".gro")
                # .ITP files
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                +group_project_name+"/"+ project_name + '/CatMec/Ligand_Parametrization/' + str(value.split('_')[0]) + ".itp",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + str(
                                    value.split('_')[0]) + ".itp")

            #copy "ATOMTYPES" file from CatMec module
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            +group_project_name+"/"+ project_name + '/CatMec/Ligand_Parametrization/atomtypes.itp',
                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + '/atomtypes.itp')

            #change DIR to Mutations list
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool+ '/' +line.strip() +'/' )
            #execute make_complex.py
            print("execute make_complex.py-----------------")
            print(make_complex_params_replaced)
            print(os.system("python3 make_complex.py " + make_complex_params_replaced))

            '''
              ____                __  __ ____    ____  _                 _       _   _                 
             |  _ \ _   _ _ __   |  \/  |  _ \  / ___|(_)_ __ ___  _   _| | __ _| |_(_) ___  _ __  ___ 
             | |_) | | | | '_ \  | |\/| | | | | \___ \| | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \/ __|
             |  _ <| |_| | | | | | |  | | |_| |  ___) | | | | | | | |_| | | (_| | |_| | (_) | | | \__ \
             |_| \_\\__,_|_| |_| |_|  |_|____/  |____/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_|___/
            
            '''

            md_mutation_folder = line.strip()
            # get slurm job ID to create dependency for upcoming jobs
            slurm_job_id = execute_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #EXECUTE MMPBSA
            '''
              ____                __  __ __  __ ____  ____ ____    _    
             |  _ \ _   _ _ __   |  \/  |  \/  |  _ \| __ ) ___|  / \   
             | |_) | | | | '_ \  | |\/| | |\/| | |_) |  _ \___ \ / _ \  
             |  _ <| |_| | | | | | |  | | |  | |  __/| |_) |__) / ___ \ 
             |_| \_\\__,_|_| |_| |_|  |_|_|  |_|_|   |____/____/_/   \_\
            
            '''
            #check if user has selected slurm as job scheduler
            # =======   get slurm key from  database   ===========
            slurm_key = "md_simulation_slurm_selection_value"
            slurm_ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                         key_name=slurm_key).latest(
                'entry_time')

            slurm_value = slurm_ProjectToolEssentials_res.key_values
            if slurm_value == "yes":
                #get command ID for input parameter
                inp_command_id = request.POST.get("command_id")
                mmpbsa_job_id = designer_slurm_queue_analyse_mmpbsa(inp_command_id, md_mutation_folder, project_name, command_tool, project_id,
                                              user_id,slurm_job_id)
            else:
                designer_queue_analyse_mmpbsa(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #EXECUTE CONTACT SCORE
            '''
               ____            _             _     ____                     
              / ___|___  _ __ | |_ __ _  ___| |_  / ___|  ___ ___  _ __ ___ 
             | |   / _ \| '_ \| __/ _` |/ __| __| \___ \ / __/ _ \| '__/ _ \
             | |__| (_) | | | | || (_| | (__| |_   ___) | (_| (_) | | |  __/
              \____\___/|_| |_|\__\__,_|\___|\__| |____/ \___\___/|_|  \___|
            '''
            if slurm_value == "yes":
                # get command ID for input parameter
                inp_command_id = request.POST.get("command_id")
                contact_score_job_id = designer_slurm_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id,mmpbsa_job_id,inp_command_id)
            else:
                designer_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #EXECUTE PATH ANALYSIS
            '''
              ____   _  _____ _   _      _    _   _    _    _  __   ______ ___ ____  
             |  _ \ / \|_   _| | | |    / \  | \ | |  / \  | | \ \ / / ___|_ _/ ___| 
             | |_) / _ \ | | | |_| |   / _ \ |  \| | / _ \ | |  \ V /\___ \| |\___ \ 
             |  __/ ___ \| | |  _  |  / ___ \| |\  |/ ___ \| |___| |  ___) | | ___) |
             |_| /_/   \_\_| |_| |_| /_/   \_\_| \_/_/   \_\_____|_| |____/___|____/ 
            '''
            if slurm_value == "yes":
                # get command ID for input parameter
                inp_command_id = request.POST.get("command_id")
                designer_slurm_queue_path_analysis(request, md_mutation_folder, project_name, command_tool, project_id,
                                             user_id,inp_command_id,contact_score_job_id)
            else:
                designer_queue_path_analysis(request, md_mutation_folder, project_name, command_tool, project_id, user_id)
            #counter for next mutant folder
            variant_index_count +=1
    return JsonResponse({'success': True})


#Hotspot module Make complex params
def hotspot_queue_make_complex_params(request, project_id, user_id, command_tool_title, command_tool, project_name):
    group_project_name = get_group_project_name(str(project_id))
    print("in  hotspot_queue_make_complex_params  definition ==================")
    # get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "hotspot_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    hotspot_mutations_file = ProjectToolEssentials_mutations_file.key_values
    print("hotspot mutation file --------")
    print("\n")
    print(hotspot_mutations_file)
    # open mutated text file and loop thru to prepare files for make_complex.py
    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              +group_project_name+"/"+ project_name + '/' + command_tool + '/' + hotspot_mutations_file, 'r'
              ) as fp_mutated_list:
        mutated_list_lines = fp_mutated_list.readlines()
        variant_index_count = 0 # mutants entry
        for line in mutated_list_lines:
            print("in mutations folder !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! and folder name is")
            print(line.strip())
            # ********** line loop in mutations file read ***********
            variant_index_dir = 0 # variant dirs counter
            for mutations_dirs in os.listdir(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              +group_project_name+"/"+ project_name + '/' + command_tool + '/' +line.strip()):
                # ---------- loop for variant dirs ---------------
                print("in mutants dir ")
                print(os.path.isdir(os.path.join(config.PATH_CONFIG[
                                                     'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/' + line.strip(),
                                                 mutations_dirs)))
                if os.path.isdir(os.path.join(config.PATH_CONFIG[
                                                  'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip(),
                                              mutations_dirs)):
                    # ------------ loop for mutations dir -----------------
                    print("print mutations_dirs")
                    print(mutations_dirs)
                    pdb_file_index_str = 0 # index for PDB (file) variant
                    for variants_dir in os.listdir(config.PATH_CONFIG[
                                                        'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs + "/"):
                        print("in variants dir ------")
                        print("variant_" + str(pdb_file_index_str) + ".pdb")
                        print(variants_dir.endswith(".pdb"))
                        print(variants_dir.strip() == "variant_" + str(pdb_file_index_str) + ".pdb")
                        # <<<<<<<<<<<<<< loop for variants dir >>>>>>>>>>>>>>>>>
                        if variants_dir.endswith(".pdb"):
                            # **************** PDB file  ********************"
                            print("with pdb dir ---------------------")
                            print(config.PATH_CONFIG[
                                      'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + variants_dir.strip())

                            # make_complex input preperation
                            # process  PDB file to get amino acids as python dict
                            ''' PDB PARSER
                                           ATOM / HETAATM  STRING line[0:6]
                                           INDEX           STRING line[6:11]
                                           ATOM TYPE       STRING line[12:16]
                                           AMINO ACID      STRING line[17:20]
                                           CHAIN ID        STRING line[21:22]
                                           RESIDUE NO      STRING line[22:26]
                                           X CO-ORDINATE   STRING line[30:38]
                                           Y CO-ORDINATE   STRING line[38:46]
                                           Z CO-ORDINATE   STRING line[46:54]
                                           '''
                            aminoacids_list = []
                            # prepare a text file of all amino acids with residue number and serial number from PDB file
                            with open(config.PATH_CONFIG[
                                          'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + variants_dir.strip(),
                                      'r'
                                      ) as fp_variant_pdb:
                                variant_pdb_lines = fp_variant_pdb.readlines()
                                for line_pdb in variant_pdb_lines:
                                    if line_pdb[0:6].strip() == "ATOM" or line_pdb[0:6].strip() == "HETAATM":
                                        if line_pdb[22:26].strip() + "_" + line_pdb[
                                                                           17:20].strip() not in aminoacids_list:
                                            # append all amino acids to list
                                            aminoacids_list.append(
                                                line_pdb[22:26].strip() + "_" + line_pdb[17:20].strip())

                            designer_protonation_matrix = ""
                            protonation_ac_list = ["ASP", "GLU", "HIS", "LYS"]
                            # copy protonation files from CatMac module to Hotspot
                            for atoms_name in protonation_ac_list:
                                try:
                                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                    +group_project_name+"/"+ project_name + '/CatMec/MD_Simulation/' + atoms_name + "_protonate.txt",
                                                    config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                    +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + atoms_name + "_protonate.txt")
                                except IOError as e:
                                    pass

                            for atoms_name in protonation_ac_list:
                                try:
                                    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                              + group_project_name+"/"+project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + atoms_name + "_protonate.txt",
                                              'r'
                                              ) as file_pointer:
                                        lines_protonation_atoms = file_pointer.readlines()
                                        for line_in_protonate_atoms in lines_protonation_atoms:
                                            if line_in_protonate_atoms.split()[1] + "_" + \
                                                    line_in_protonate_atoms.split()[
                                                        0] not in aminoacids_list:
                                                pass
                                            else:
                                                designer_protonation_matrix += line_in_protonate_atoms
                                except IOError as e:
                                    pass

                            # remove protonations input and matrix files if exsist
                            try:
                                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                          +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt')
                                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                          +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/protonate_input.txt')
                            except:
                                pass

                            # prepare final matrix file of protonation values
                            try:
                                outFile = open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                               +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt',
                                               'w+')
                                outFile.write(designer_protonation_matrix)
                                outFile.close()
                            except IOError as (errno, strerror):
                                print("I/O error({0}): {1}".format(errno, strerror))

                            # prepare final protonation input text file
                            with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                      +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/protonate_input.txt',
                                      'w+'
                                      ) as input_file_ptr:
                                with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                          +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt',
                                          'r'
                                          ) as matrix_file_ptr:
                                    matrix_file_lines = matrix_file_ptr.readlines()
                                    for matrix_file_line in matrix_file_lines:
                                        input_file_ptr.write(matrix_file_line.split()[-1] + '\n')

                            # get python script for make_compex execution
                            shutil.copyfile(
                                config.PATH_CONFIG['shared_scripts'] + 'CatMec/MD_Simulation/' + "make_complex.py",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                +group_project_name+"/"+ project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + "/" + "make_complex.py")

                            # get make_complex parameters from DB
                            try:
                                make_complex_params_keyname = "make_complex_parameters"
                                ProjectToolEssentials_make_complex_params = \
                                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=make_complex_params_keyname).latest(
                                        'entry_time')
                                make_complex_params = ProjectToolEssentials_make_complex_params.key_values
                            except db.OperationalError as e:
                                db.close_old_connections()
                                make_complex_params_keyname = "make_complex_parameters"
                                ProjectToolEssentials_make_complex_params = \
                                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=make_complex_params_keyname).latest(
                                        'entry_time')
                                make_complex_params = ProjectToolEssentials_make_complex_params.key_values


                            variant_protien_file = 'variant_' + str(variant_index_count) + '.pdb'
                            # replace protien file in make_complex_params
                            make_complex_params_replaced = re.sub(r'(\w+)(\.pdb)', variants_dir.strip(),
                                                                  make_complex_params)
                            print("make_complex_params_replaced")
                            print(make_complex_params_replaced)
                            # copy ligand .GRO files and .ITP files from CatMec module
                            ligands_key_name = 'substrate_input'
                            ProjectToolEssentials_ligand_name_res = ProjectToolEssentials.objects.all().filter(
                                project_id=project_id,
                                key_name=ligands_key_name).latest(
                                'entry_time')
                            ligand_names = ProjectToolEssentials_ligand_name_res.key_values
                            ligand_file_data = ast.literal_eval(ligand_names)
                            ligand_names_list = []
                            for key, value in ligand_file_data.items():
                                # value.split('_')[0] is ligand name
                                ligand_names_list.append(value.split('_')[0])

                                # .ITP files
                                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                +group_project_name+"/"+ project_name + '/CatMec/Ligand_Parametrization/' + str(
                                    value.split('_')[0]) + ".itp",
                                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + str(
                                                    value.split('_')[0]) + ".itp")


                                # copying ligand files
                                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                +group_project_name+"/"+ project_name + '/' + command_tool + '/'+"frames_"+str(mutations_dirs.strip()[-1])+"/"+value.split('_')[0]+".pdb",
                                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" +value.split('_')[0]+".pdb")

                                '''
                                Process protien PDB file
                                - generate ligand.gro files
                                '''
                                # creating .GRO files for ligands
                                os.system("gmx editconf -f " + config.PATH_CONFIG[
                                    'local_shared_folder_path_project'] + 'Project/' + group_project_name+"/"+project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" +
                                          value.split('_')[0] + ".pdb" + " -o " + config.PATH_CONFIG[
                                              'local_shared_folder_path_project'] + 'Project/' +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" +
                                          value.split('_')[0] + ".gro")



                            # copy "ATOMTYPES" file from CatMec module
                            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                            + project_name + '/CatMec/Ligand_Parametrization/atomtypes.itp',
                                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                            +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + 'atomtypes.itp')

                            # change DIR to Mutations list
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + command_tool + '/' + line.strip() + '/' + mutations_dirs.strip() + "/")
                            # execute make_complex.py
                            print("execute make complex")
                            print(os.getcwd())
                            print("command is ----------------")
                            print(make_complex_params_replaced)
                            os.system("python3 make_complex.py "+make_complex_params_replaced)
                            '''
                              ____                __  __ ____    ____  _                 _       _   _                 
                             |  _ \ _   _ _ __   |  \/  |  _ \  / ___|(_)_ __ ___  _   _| | __ _| |_(_) ___  _ __  ___ 
                             | |_) | | | | '_ \  | |\/| | | | | \___ \| | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \/ __|
                             |  _ <| |_| | | | | | |  | | |_| |  ___) | | | | | | | |_| | | (_| | |_| | (_) | | | \__ \
                             |_| \_\\__,_|_| |_| |_|  |_|____/  |____/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_|___/

                            '''

                            md_mutation_folder = line.strip()
                            variant_dir_md = mutations_dirs.strip()
                            execute_hotspot_md_simulation(request, md_mutation_folder, project_name, command_tool,
                                                          project_id,
                                                          user_id, variant_dir_md)

                        pdb_file_index_str += 1
                variant_index_dir += 1
            #Execute MMPBSA (In mutations folder)
            '''
              ____                __  __ __  __ ____  ____ ____    _    
             |  _ \ _   _ _ __   |  \/  |  \/  |  _ \| __ ) ___|  / \   
             | |_) | | | | '_ \  | |\/| | |\/| | |_) |  _ \___ \ / _ \  
             |  _ <| |_| | | | | | |  | | |  | |  __/| |_) |__) / ___ \ 
             |_| \_\\__,_|_| |_| |_|  |_|_|  |_|_|   |____/____/_/   \_\

            '''
            mutation_dir_mmpbsa = line.strip()
            hotspot_analyse_mmpbsa(request,mutation_dir_mmpbsa, project_name, command_tool, project_id, user_id)

            variant_index_count += 1



#Designer MMPBSA module
class Designer_Mmpbsa_analyse(APIView):
    def get(self,request):
        pass

    def post(self,request):
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        user_id = commandDetails_result.user_id
        QzEmployeeEmail_result = QzEmployeeEmail.objects.get(qz_user_id=user_id)
        email_id = QzEmployeeEmail_result.email_id
        dot_Str_val = email_id.split('@')[0]
        lenght_of_name_with_dots = len(dot_Str_val.split("."))
        user_email_string = ""
        for i in range(lenght_of_name_with_dots):
            user_email_string += dot_Str_val.split(".")[i] + " "

        group_project_name = get_group_project_name(str(project_id))
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id, user_email_string)

        makdir_designer_analysis(project_name,project_id)

        key_name_indexfile_input = 'designer_mmpbsa_index_file_dict'

        #get list of index file options for gmx input
        ProjectToolEssentials_res_indexfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_indexfile_input).latest('entry_time')

        #get list of .XTC files from different MD runs to execute "gmx trjcat " command
        key_name_xtcfile_input = 'designer_mmpbsa_md_xtc_file_list'

        ProjectToolEssentials_res_xtcfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_xtcfile_input).latest('entry_time')

        #get .tpr file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_tpr_file = 'designer_mmpbsa_tpr_file'

        ProjectToolEssentials_res_tpr_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_tpr_file).latest('entry_time')
        md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.key_values.replace('\\', '/')

        # get .ndx file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_ndx_file = 'designer_mmpbsa_index_file'

        ProjectToolEssentials_res_ndx_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ndx_file).latest('entry_time')
        md_simulations_ndx_file = ProjectToolEssentials_res_ndx_file_input.key_values.replace('\\', '/')

        key_name_CatMec_input = 'substrate_input'
        command_tootl_title = "CatMec"
        # get list of ligand inputs
        ProjectToolEssentials_res_CatMec_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                       key_name=key_name_CatMec_input).latest('entry_time')
        CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.key_values)
        # if User has only one ligand as input
        multiple_ligand_input = False
        if len(CatMec_input_dict) > 1:
            multiple_ligand_input = True

        indexfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_indexfile_input.key_values)
        xtcfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_xtcfile_input.key_values)

        '''
                                                                  .                o8o                         .        
                                                        .o8                `"'                       .o8        
         .oooooooo ooo. .oo.  .oo.   oooo    ooo      .o888oo oooo d8b    oooo  .ooooo.   .oooo.   .o888oo      
        888' `88b  `888P"Y88bP"Y88b   `88b..8P'         888   `888""8P    `888 d88' `"Y8 `P  )88b    888        
        888   888   888   888   888     Y888'           888    888         888 888        .oP"888    888        
        `88bod8P'   888   888   888   .o8"'88b          888 .  888         888 888   .o8 d8(  888    888 .      
        `8oooooo.  o888o o888o o888o o88'   888o        "888" d888b        888 `Y8bod8P' `Y888""8o   "888"      
        d"     YD                                                          888                                  
        "Y88888P'                                                      .o. 88P                                  
                                                                       `Y888P                                           
        '''
        #if len(xtcfile_input_dict) > 1:
        md_xtc_files_str = ""
        #mmpbsa_project_path
        for xtcfile_inputkey, xtcfile_inputvalue in xtcfile_input_dict.iteritems():
            xtcfile_inputvalue_formatted = xtcfile_inputvalue.replace('\\', '/')
            md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + \
                                config.PATH_CONFIG['designer_md_simulations_path'] + xtcfile_inputvalue_formatted + " "
        gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] + group_project_name+"/"+project_name + '/Designer/' + config.PATH_CONFIG[
                             'designer_mmpbsa_path'] + "merged.xtc -keeplast -cat"
        os.system(gmx_trjcat_cmd)

        '''
                                                                                          oooo                                                .o8              
                                                                                  `888                                               "888              
         .oooooooo ooo. .oo.  .oo.   oooo    ooo      ooo. .oo.  .oo.    .oooo.    888  oooo   .ooooo.              ooo. .oo.    .oooo888  oooo    ooo 
        888' `88b  `888P"Y88bP"Y88b   `88b..8P'       `888P"Y88bP"Y88b  `P  )88b   888 .8P'   d88' `88b             `888P"Y88b  d88' `888   `88b..8P'  
        888   888   888   888   888     Y888'          888   888   888   .oP"888   888888.    888ooo888              888   888  888   888     Y888'    
        `88bod8P'   888   888   888   .o8"'88b         888   888   888  d8(  888   888 `88b.  888    .o              888   888  888   888   .o8"'88b   
        `8oooooo.  o888o o888o o888o o88'   888o      o888o o888o o888o `Y888""8o o888o o888o `Y8bod8P' ooooooooooo o888o o888o `Y8bod88P" o88'   888o 
        d"     YD                                                                                                                                      
        "Y88888P'                                                                                                                                      
        '''
        if multiple_ligand_input:
            #for multiple ligand input
            print("for multiple ligand input")
            #get user input ligand name from DB
            key_name_ligand_input = 'designer_mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.key_values
            #extract ligand number
            if "[ " + ligand_name + " ]" in indexfile_input_dict.keys():
                ligand_name_input = str(indexfile_input_dict["[ "+ligand_name+" ]"])
            indexfile_complex_option_input = ""
            indexfile_receptor_option_input = ""
            #prepare receptor option input string
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name_split = ligand_inputvalue.split("_")
                dict_ligand_name = ligand_name_split[0]
                if "[ "+dict_ligand_name+" ]" in indexfile_input_dict.keys() and dict_ligand_name != ligand_name:
                    indexfile_receptor_option_input += str(indexfile_input_dict["[ "+dict_ligand_name+" ]"]) +" | "
             #prepare complex option input string
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name_split = ligand_inputvalue.split("_")
                dict_ligand_name = ligand_name_split[0]
                if "[ "+dict_ligand_name+" ]" in indexfile_input_dict.keys():
                    indexfile_complex_option_input += str(indexfile_input_dict["[ "+dict_ligand_name+" ]"]) +" | "

            if "[ Protein ]" in indexfile_input_dict.keys():
                indexfile_complex_option_input += str(indexfile_input_dict["[ Protein ]"])
                indexfile_receptor_option_input += str(indexfile_input_dict["[ Protein ]"])
            #reverse the strings
            indexfile_complex_option_input = indexfile_complex_option_input.split(" | ")
            indexfile_complex_option_input = indexfile_complex_option_input[-1::-1]
            reversed_indexfile_complex_option_input = ' | '.join(indexfile_complex_option_input)

            indexfile_receptor_option_input = indexfile_receptor_option_input.split(" | ")
            indexfile_receptor_option_input = indexfile_receptor_option_input[-1::-1]
            reversed_indexfile_receptor_option_input = ' | '.join(indexfile_receptor_option_input)
            print(reversed_indexfile_complex_option_input)
            print(reversed_indexfile_receptor_option_input)
            maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
            protien_ligand_complex_index = receptor_index + 1
            #write protien ligand complex index number to DB
            entry_time = datetime.now()
            key_name_protien_ligand_complex_index = 'designer_mmpbsa_index_file_protien_ligand_complex_number'
            ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(tool_title=commandDetails_result.command_tool,
                                                                                      project_id=project_id,
                                                                                      key_name=key_name_protien_ligand_complex_index,
                                                                                      key_values=protien_ligand_complex_index,
                                                                                      entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            ligand_name_index = protien_ligand_complex_index + 1
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                                               'designer_md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(
                str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(reversed_indexfile_complex_option_input) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n"+str(ligand_name_input)+"\nname "+str(ligand_name_index)+" ligand"+ "\nq\n")
            file_gmx_make_ndx_input.close()

            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + config.PATH_CONFIG[
                               'designer_mmpbsa_path'] + "index.ndx < " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + "gmx_make_ndx_input.txt"

            print(" make index command")
            print(gmx_make_ndx)
            os.system(gmx_make_ndx)

        else:
            #for single ligand input
            #get ligand name
            ligand_name = ""
            for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                ligand_name = ligand_inputvalue.split("_")[0]
            #prepare input file for gmx make_ndx command
            protein_index = 0
            ligandname_index = 0
            for indexfile_inputkey, indexfile_inputvalue in indexfile_input_dict.iteritems(): # key is index option text and value is index number
                if ligand_name in indexfile_inputkey:
                    ligandname_index = indexfile_inputvalue
                if "[ Protein ]" == indexfile_inputkey:
                    protein_index = indexfile_inputvalue
            maximum_key_ndx_input = max(indexfile_input_dict,key=indexfile_input_dict.get)
            #print indexfile_input_dict[maximum_key_ndx_input]
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] +1
            protien_ligand_complex_index = receptor_index + 1
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                                              'designer_md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(str(protein_index)+"\nname "+str(receptor_index)+" receptor\n"+str(protein_index)+" | "+str(ligandname_index)+"\nname "+str(protien_ligand_complex_index)+" complex")
            file_gmx_make_ndx_input.close()
            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + config.PATH_CONFIG[
                               'designer_mmpbsa_path'] + "complex_index.ndx <"+config.PATH_CONFIG[
                                              'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                                              'designer_md_simulations_path'] + "gmx_make_ndx_input.txt"

            print(" make index command")
            print(gmx_make_ndx)
            os.system(gmx_make_ndx)

        perform__designer_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file)
        #===================   post processing after make index  ===============================
        # copy MD .tpr file to MMPBSA working directory
        source_tpr_md_file = config.PATH_CONFIG[
                                 'local_shared_folder_path'] + group_project_name+"/"+project_name + '/' + config.PATH_CONFIG[
                                 'designer_md_simulations_path'] + md_simulations_tpr_file
        tpr_file_split = md_simulations_tpr_file.split("/")
        dest_tpr_md_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                           config.PATH_CONFIG['designer_mmpbsa_path'] + tpr_file_split[1]

        shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

        # copy topology file from MS to MMPBSA working directory
        source_topology_file = config.PATH_CONFIG[
                                   'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                                   'designer_md_simulations_path'] + tpr_file_split[0] + "/topol.top"
        dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                             config.PATH_CONFIG['designer_mmpbsa_path'] + "topol.top"
        shutil.copyfile(source_topology_file, dest_topology_file)

        # copy ligand .itp files
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            source_itp_file = config.PATH_CONFIG[
                                  'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                                  'designer_md_simulations_path'] + tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
            dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path'] + ligand_name_split[0] + ".itp"
            shutil.copyfile(source_itp_file, dest_itp_file)


        key_name_ligand_input = 'designer_mmpbsa_input_ligand'
        # processing itp files
        pre_process_designer_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input)

        # ----------------------   make a "trail" directory for MMPBSA   -----------------------
        os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                  config.PATH_CONFIG['designer_mmpbsa_path'] + "trial")
        # copying MMPBSA input files to trail directory
        # copy .XTC file
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                        config.PATH_CONFIG['designer_mmpbsa_path'] + "merged-recentered.xtc",
                        config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                        config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/npt.xtc")

        # copy other input files for MMPBSA
        for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path']):
            # copy .TPR file
            if file_name.endswith(".tpr"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/npt.tpr")
            # copy .NDX file
            if file_name.endswith(".ndx"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/index.ndx")

            # copy .TOP file
            if file_name.endswith(".top"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/"+file_name)
            # copy .ITP files
            if file_name.endswith(".itp"):
                # renaming user input ligand as LIGAND
                key_name_ligand_input = 'designer_mmpbsa_input_ligand'

                ProjectToolEssentials_res_ligand_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_ligand_input).latest('entry_time')
                ligand_name = ProjectToolEssentials_res_ligand_input.key_values
                if file_name[:-4] == ligand_name:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/ligand.itp")
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/"+file_name)
                else:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/" + file_name)

        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] +group_project_name+"/"+ project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'])
        os.system("sh "+config.PATH_CONFIG['GMX_run_file_one'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])
        return JsonResponse({"success": True})

        '''primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
        #MD simulations shared path
        md_simulations_sharedpath = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + '/CatMec/MD_Simulation/'
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' +"Analysis/mmpbsa" + '/')
        print os.system("pwd")
        print os.getcwd()
        print "=========== title is =============="
        print commandDetails_result.command_title


        process_return = execute_command(primary_command_runnable,inp_command_id)

        command_title_folder = commandDetails_result.command_title

        out, err = process_return.communicate()
        process_return.wait()
        print "process return code is "
        print process_return.returncode
        if process_return.returncode == 0:
            print "inside success"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print "inside error"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})'''


def makdir_designer_analysis(project_name,project_id):
    # create analysis directory for MMPBSA , Contact Score and PathAnalysis execution
    group_project_name = get_group_project_name(str(project_id))
    try:
        os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] +group_project_name+"/"+ project_name + '/' + config.PATH_CONFIG[
                     'designer_md_simulations_path'] + "Analysis/")
    except OSError as e:  # except path error
        if e.errno != os.errno.EEXIST:
            # directory already exists
            pass
        else:
            print(e.errno)
            pass


#alter grid.gpf file with respective .PDBQT file paths
def process_grid_file(commandDetails_result,QzwProjectDetails_res,request):
    enzyme_file_name =""

    #get output enzyme PDBQT file name
    grid_fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/grid.gpf','r')
    for line in grid_fileobj:
        if re.search("pdbqt", line):
            keyword = ".pdbqt"
            befor_keyowrd, keyword, after_keyword = line.partition(keyword)
            keyword2 = "receptor "
            befor_keyowrd2, keyword2, after_keyword2 = befor_keyowrd.partition(keyword2)
            enzyme_file_name = after_keyword2
    PDBQT_dir = config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/'
    #read grid file
    for root, dirs, files in os.walk(PDBQT_dir):  # replace the . with your starting directory
        for file in files:
            if file.endswith(".pdbqt"):
                filelst = []
                if file ==  enzyme_file_name+'.pdbqt':
                    grid_fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name +'/'+commandDetails_result.command_tool + '/grid.gpf','r+')
                    for line in grid_fileobj:
                        if re.search('map '+enzyme_file_name, line):
                            line =re.sub('map '+enzyme_file_name,'map '+config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool +'/'+enzyme_file_name,line)
                            filelst.append(line)
                        elif re.search('gridfld '+enzyme_file_name, line):
                            line = re.sub('gridfld ' + enzyme_file_name, 'gridfld ' + config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/' + enzyme_file_name,line)
                            filelst.append(line)
                        elif re.search(enzyme_file_name+'.pdbqt', line):
                            line = re.sub(enzyme_file_name+'.pdbqt',config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/'+enzyme_file_name+'.pdbqt',line)
                            filelst.append(line)
                        else:
                            filelst.append(line)

                myfile = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/grid.gpf', 'w')
                myfile.writelines(filelst)
    print("before return")
    return True
#alter dock.dpf file with respective .PDBQT file paths
def process_dock_file(commandDetails_result,QzwProjectDetails_res,request):
    print("in process dock file")
    ligand_file_name =""
    enzyme_file_name =""
    #get output enzyme PDBQT file name
    dock_fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/dock.dpf','r')
    for line in dock_fileobj:
        if re.search("pdbqt", line):
            keyword = ".pdbqt"
            befor_keyowrd, keyword, after_keyword = line.partition(keyword)
            keyword2 = "move "
            befor_keyowrd2, keyword2, after_keyword2 = befor_keyowrd.partition(keyword2)
            ligand_file_name = after_keyword2
    dock_fileobj.close()
    PDBQT_dir = config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/'
    print(PDBQT_dir)
    #read grid file
    for root, dirs, files in os.walk(PDBQT_dir):  # replace the . with your starting directory
        for file in files:
            if file.endswith(".pdbqt"):
                filelst = []
                dock_fileobj3 = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/dock.dpf','r+')
                if file !=  ligand_file_name+'.pdbqt':
                    print("in HPMAE enzyme")
                    enzyme_file_name = file
                else:
                    pass
                for line in dock_fileobj3:
                    print("inside sinfle dockobj3")
                    if re.search('map ' + enzyme_file_name[:-6], line):
                        line = re.sub('map ' + enzyme_file_name[:-6], 'map ' + config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/' + enzyme_file_name[:-6],line)
                        filelst.append(line)
                    elif re.search('fld ' + enzyme_file_name[:-6], line):
                        line = re.sub('fld ' + enzyme_file_name[:-6], 'fld ' + config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/' + enzyme_file_name[:-6],line)
                        filelst.append(line)
                    elif re.search('move ' +ligand_file_name+'.pdbqt', line):
                        line = re.sub('move ' + ligand_file_name+'.pdbqt', 'move ' + config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/' +ligand_file_name+'.pdbqt',line)
                        filelst.append(line)
                    else:
                        filelst.append(line)

                myfile = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/dock.dpf', 'w')
                myfile.writelines(filelst)

def move_outputFiles(moveFile_source,moveFile_destination):
    print("inside move outputfiles")
    for root, dirs, files in os.walk(moveFile_source):
        for file in files:
            path_file = os.path.join(root, file)
            os.system("cp "+path_file+" "+moveFile_destination)
    return True


def move_topolfile_(topolfile_source,topolfile_destination):
    os.system("cp " + topolfile_source+ " " + topolfile_destination)

@csrf_exempt
def move_files_(inp_command_id):
    commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
    project_id = commandDetails_result.project_id
    group_project_name = get_group_project_name(str(project_id))
    QzwProjectDetails_res =QzwProjectDetails.objects.get(project_id=project_id)
    project_name = QzwProjectDetails_res.project_name
    source = config.PATH_CONFIG['local_qzw_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/'
    destination = config.PATH_CONFIG['local_shared_folder_path']+group_project_name+"/"+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/'
    shared_loc_copy_res= copytree(source, destination, symlinks=False, ignore=None)


def copytree(source, destination, symlinks=False, ignore=None):
    # for item in os.listdir(src):
    #     s = os.path.join(src, item)
    #     d = os.path.join(dst, item)
    #     if os.path.isdir(s):
    #         if os.path.exists(s):
    #             pass
    #         else:
    #             shutil.copytree(s, d)
    #     else:
    #         shutil.copy(s, d)
    for root, dirs, files in os.walk(source):  # replace the . with your starting directory

        for file in files:
            if file.endswith(".log"):
                #copy files to logfiles folder
                path_file = os.path.join(root, file)
                print(path_file)
                print(destination)
                #print shutil.copy(path_file, destination+"")
            #path_file = os.path.join(root, file)
            #print shutil.copy(path_file, destination)  # change you destination dir
            #print os.system("cp "+path_file+" "+destination)
            

def extract_user_name_from_email(email_id):
    dot_Str_val = email_id.split('@')[0]
    lenght_of_name_with_dots = len(dot_Str_val.split("."))
    name_of_employee = ""
    for i in range(lenght_of_name_with_dots):
        name_of_employee += dot_Str_val.split(".")[i] + " "
    print(name_of_employee)
    return name_of_employee


def send_non_slurm_email(inp_command_id,status_id,project_name,project_id,command_tool,command_title,job_id=''):
    print("inside send_non_slurm_email function")
    print("*****************************************************************************************")
    print("inp_command_id is ",inp_command_id)
    print("status_id is ",status_id)
    print("job_id is ",job_id)
    commandDetails_res = commandDetails.objects.all().filter(command_id=inp_command_id).latest(
        'entry_time')
    command_title = commandDetails_res.command_title
    print("command_title is ",command_title)
    user_id = str(commandDetails_res.user_id)
    print("user_id is ",user_id)
    QzEmployeeEmail_res = QzEmployeeEmail.objects.get(qz_user_id=user_id)
    #print("user_email_string")
    #print(user_email_string)
    #print("QzEmployeeEmail_res")
    #print(QzEmployeeEmail_res)
    #print(type(QzEmployeeEmail_res))
    email_id = QzEmployeeEmail_res.email_id
    print("email_id is ",email_id)
    print("*****************************************************************************************")
    entry_time = datetime.now()
    #local_time = entry_time.strftime("%x %X")
    local_time = entry_time.strftime("%m/%d/%Y, %H:%M:%S")
    user_name = str(extract_user_name_from_email(str(email_id)))
    slurm_job = "Yes"
    # if (command_tool == "Thermostability") or (command_tool == "TASS" and command_title == "gromacs_to_amber") or (command_tool == "CatMecandAutodock" and command_title == "Dockinganddocking_post_analysis") or (command_tool == "CatMecandAutodock" and command_title == "Dockingandmake_gpf_dpf") or (command_tool == "CatMecandAutodock" and command_title == "DockingandPdbtoPdbqt"):
    if(command_tool == "TASS" and command_title == "gromacs_to_amber") or (command_tool == "CatMecandAutodock" and command_title == "Dockinganddocking_post_analysis") or (command_tool == "CatMecandAutodock" and command_title == "Dockingandmake_gpf_dpf") or (command_tool == "CatMecandAutodock" and command_title == "DockingandPdbtoPdbqt"):
        slurm_job = "No"

    if status_id == 1:
        status = "submitted the job for execution"
        new_message = "you will receive another completion notification email update, after the job is executed"
    elif status_id == 2:
        if slurm_job == "Yes":
            status = "Preparation of Slurm Script is in progress"
        else:
            status = "started to execute"
        new_message = "you will receive another completion notification email update, after the job is executed"
    elif status_id == 3:
        if slurm_job == "Yes":
            status = "Job Submitted Through Slurm"
        else:
            status = "executed successfully"
        new_message = ""
    elif status_id == 4:
        if slurm_job == "Yes":
            status = "Slurm Job Submission failed"
        else:
            status = "executed unsuccessful"
        new_message = ""
    # if status_id == 2:
    #     status = "started to execute"
    # elif status_id == 3:
    #     status = "executed successfully"
    # elif status_id == 4:
    #     status = "executed unsuccessful"
    entry_time = str(datetime.now())
    if job_id != '':inp_command_id = job_id
    #table_design = "<html><head><style>td,th{border: 1px solid;padding: 8px;}</style></head><body><table><tr><th><center>User Name</center></th><th><center>Job Name</center></th><th><center>Status</center></th><th><center>Time</th></tr><tr><td>" + user_email_string + "</td><td>" + command_title + "</td><td style='color:red'>" + status + "</td><td>" + entry_time + "</td></tr></table></body></html>"
    table_design = """
    <html>
        <head>
            <style>td,th{border: 1px solid;padding: 8px;} table{border-spacing: 0px;border-collapse: collapse;}</style>
        </head>
        <body>
        <p> Dear """+str(user_name)+""",</p>
        <p>This is a mail to notify about the """+str(command_title)+""" job submitted using QZyme WorkBench is started to execute, and the details of the job are as follows</p>
            <table>
                <tr>
                    <th><center>Project Name</center></th>
                    <th><center>Module Name</center></th>
                    <th><center>Sub Module Name</center></th>
                    <th><center>Server</center></th>
                    <th><center>Job ID</center></th>
                    <th><center>Submitted By</center></th>
                    <th><center>Time</center></th>
                    <th><center>Status</center></th>
                    <th><center>Slurm Job</center></th>
                </tr>
                <tr>
                    <td>""" + str(project_name) + """</td>
                    <td>""" + str(command_tool) + """</td>
                    <td>""" + str(command_title) + """</td>
                    <td>QZyme2</td>
                    <td>""" + str(inp_command_id) + """</td>
                    <td>""" + str(user_name) + """</td>
                    <td>""" + str(local_time) + """</td>
                    <td style='color:red'>""" + str(status) + """</td>
                    <td>""" +str(slurm_job)+"""</td>
                </tr>
            </table>
            <p>"""+new_message+"""</p>
        </body>
    </html>
    """


    '''currently commenting as quantumzyme email are being blocked when sent using scripts
    SMTPserver = 'quantumzyme.com'
    sender = 'varadharaj.ranganatha@quantumzyme.com'
    destination = ['varadharaj.ranganatha@quantumzyme.com',email_id]

    USERNAME = "qzwebgo"
    PASSWORD = "Qzyme@786"'''
    SMTPserver = 'smtp.gmail.com'
    #sender = 'testsendingemailusingpython@gmail.com'
    sender = 'workbench.notification@gmail.com'
    destination = [email_id]

    #USERNAME = "testsendingemailusingpython@gmail.com"
    #PASSWORD = "ysfpsehpndheivem"
    USERNAME = "workbench.notification@gmail.com"
    PASSWORD = "ekdbspktyqjunpuf"

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'html'


    content= table_design

    subject=project_name+" Notification(QZyme WorkBench)"

    import sys
    import os
    import re

    from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
    # from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)

    # old version
    # from email.MIMEText import MIMEText
    from email.mime.text import MIMEText

    try:
        msg = MIMEText(content, text_subtype)
        msg['Subject']=subject
        msg['From']= sender # some SMTP servers will do this automatically, not all

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(True)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.quit()
    except Exception as e:
        print("exception is ",str(e))
    #except:
    #    sys.exit( "mail failed; %s" % "CUSTOM_ERROR" ) # give an error message


def update_command_status(inp_command_id,status_id,user_email_string,project_name, project_id,command_tool,command_title,job_id=''):
    print("updating command execution status")
    #check if process initiated

    entry_time = datetime.now()
    updated_status = False
    if status_id == 2:
        try:
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_started_at=entry_time)
            updated_status = True
            #send_non_slurm_email(inp_command_id, status_id, project_name, project_id,command_tool,command_title)

            
        except db.OperationalError as e:
            db.close_old_connections()
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_started_at=entry_time)

    if status_id == 3:
        try:
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_completed_at=entry_time)
            updated_status = True
            #send_non_slurm_email(inp_command_id, status_id, project_name, project_id,command_tool,command_title)
        except db.OperationalError as e:
            db.close_old_connections()
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_completed_at=entry_time)

    if status_id == 4:
        try:
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_completed_at=entry_time)
            updated_status = True
            #send_non_slurm_email(inp_command_id, status_id, project_name, project_id,command_tool,command_title)
        except db.OperationalError as e:
            db.close_old_connections()
            QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(
                status=status_id,
                execution_completed_at=entry_time)
    print("updated_status is *********************************************************")
    print(updated_status)
    print("updated_status is *********************************************************")
    # VVVVVVVVVVVVVVVVVAAAAAAAAAAAAAAARRRRRRRRRRRRRRRAAAAAAAAAAAAAAAADDDDDDDDDDDDDDDDDDDDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    if updated_status:
        pass
        #send_non_slurm_email(inp_command_id, status_id, project_name, project_id,command_tool,command_title,job_id)
    print("result of update command execution status")
    print(QzwProjectDetails_update_res)
    return True

#process science direct data crawler
def get_crawler_data(start_offset,search_keyword):
    url = 'https://www.sciencedirect.com/search'+start_offset
    print("http URL is -")
    print(url)

    soup = BeautifulSoup(urlopen(url),"html.parser")
    for range_tag in soup.find_all('li', {'class': 'next-link'}):
        print("in first loop")
        for rangespantag in range_tag.find_all('a'):
            print("in second loop")
            if rangespantag.text == "next":
                get_next_page(rangespantag.attrs['href'])
                print("if next tag exists")
                data_class_variable =  {'class' : 'ResultItem'}
                data_attr_variable = soup.findAll(attrs=data_class_variable)

                for looping_data in data_attr_variable:
                    print("in looping data")
                    print("title is-")
                    print(looping_data.h2.text.encode('utf-8').strip())
                    title = looping_data.h2.text.encode('utf-8').strip()
                    journal = looping_data.find(class_='subtype-srctitle-link').text.encode('utf-8').strip()
                    author = looping_data.find(class_='Authors').text.encode('utf-8').strip()
                    doi = looping_data['data-doi'].encode('utf-8').strip()
                    QzwResearchPapers_create = QzwResearchPapers.objects.create(
                        research_paper_title=looping_data.h2.text,
                        research_paper_url="",
                        research_paper_citations="",
                        research_paper_version="",
                        research_paper_doi=looping_data['data-doi'],
                        research_paper_pdf_link="",
                        research_paper_keywords=search_keyword,
                        research_paper_abstract="",
                        publication_year="",
                        author_name=looping_data.find(class_='Authors').text,
                        journal_name=looping_data.find(class_='subtype-srctitle-link').text,)


            else:
                exit()
    return True

def get_initial_crawler_data(base_page,start_page,search_keyword):
    data = []
    print("in crawler initial fetch")
    base_url = 'https://www.sciencedirect.com/search'+base_page
    res = requests.get(base_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
    soup = BeautifulSoup(res.text,"html.parser",from_encoding="iso-8859-1")
    print("*******************pagination data is *********************")
    paginationsdata_list = soup.select('ol.Pagination > li')[0].get_text(strip=True)
    print(paginationsdata_list)
    page_offset_keyword = "Page1of"
    before_offset_keyword,page_offset_keyword,after_offset_keyword = paginationsdata_list.partition(page_offset_keyword)
    print("================  pagination count is =================================")
    print(after_offset_keyword)
    start_offset = 0
    for page_count in range(1,int(after_offset_keyword)):
        print("=============== page count is =======================")
        print(page_count)
        page_url = 'https://www.sciencedirect.com/search/api'+start_page+str(start_offset)
        print("================ page URL is =========================")
        print(page_url)
        url_json_content = requests.get(page_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
        for paper_data in url_json_content['searchResults']:
            authors = []
            authors_str_data = ""
            title = paper_data['title'].encode('utf-8')
            try:
                journal = paper_data['sourceTitle']
            except Exception as j:
                journal = ""
            try:
                doi = str(paper_data['doi'])
            except Exception as e:
                doi = ""
                # pass
            try:
                for authors_data in paper_data['authors']:
                    authors.append(authors_data['name'])
                authors_str_data = ' '.join(authors)
            except Exception as a:
                authors = ""

            QzwResearchPapers_create = QzwResearchPapers.objects.create(
                research_paper_title=title,
                research_paper_doi=doi,
                research_paper_pdf_link=paper_data['link'],
                research_paper_keywords=search_keyword,
                author_name=authors_str_data,
                journal_name=journal,
                search_source="Science Direct")
        start_offset += 100


def get_crawler_data_gs(search_keyword,encoded_search_keyword):
    print("in crawler google")
    for page_count in range(1, 990):
        print("=============== page count is =======================")
        print(page_count)
        page_url = 'https://scholar.google.co.in/scholar?start=' + str(page_count)+'&q='+encoded_search_keyword+'&hl=en&as_sdt=0,5'
        print("================ page URL is =========================")
        print(page_url)
        url_content = requests.get(page_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
        soup = BeautifulSoup(url_content.text, "html.parser", from_encoding="iso-8859-1")
        for range_tag in soup.findAll('div',{'class':'gs_r'}):
            try:
                title = range_tag.h3.get_text().encode('utf-8').strip()
            except Exception as e:
                title = ""
            print(title)
            print("================= anchor link is ================")
            try:
                paper_link = range_tag.h3.a['href'].encode('utf-8').strip()
            except Exception as a_href:
                paper_link= ""
            print("================= authors are ===================")
            try:
                authors_data= range_tag.find('div', {'class': 'gs_a'}).get_text().encode("utf-8")
            except Exception as authors:
                authors_data = ""

            QzwResearchPapers_create = QzwResearchPapers.objects.create(
                research_paper_title=title,
                research_paper_doi="",
                research_paper_pdf_link=paper_link,
                research_paper_keywords=search_keyword,
                author_name=authors_data,
                journal_name="",
                search_source="Google Scholar")

#pubmed crawler
def get_crawler_data_pmd(search_keyword,encoded_search_keyword):
    print("in pubmed crawler")
    initial_page_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=&term="+str(encoded_search_keyword)
    print("---------------- initial page URL is --------------------")
    print(initial_page_url)
    url_content = requests.get(initial_page_url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
    print("-------------- json content is --------------------")
    print(url_content)
    #get total id_list count
    count_id_list = url_content['esearchresult']['count']
    print("------------- id count is --------------")
    print(count_id_list)
    #call API to get all ids list with total count if ids list
    page_url_count_all = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax="+str(count_id_list)+"&term=" + str(encoded_search_keyword)
    page_url_count_allcontent = requests.get(page_url_count_all, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()

    for id_s in page_url_count_allcontent['esearchresult']['idlist']:
        fetch_paper_details_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id=" + str(
            id_s)
        print("------------------ IDS URL is -----------------------")
        print(fetch_paper_details_url)
        paper_details_content = requests.get(fetch_paper_details_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
        for data_json_key, data_json_val in paper_details_content['result'][id_s].iteritems():
            authors_list =[]
            title = ""
            doi = ""
            journal= ""
            authors_str_data = ""
            if data_json_key == "title":
                print(data_json_val.encode("utf-8"))
                try:
                    title = data_json_val.encode('utf-8')
                except Exception as e:
                    title = ""
            if data_json_key == "elocationid":
                print(data_json_val.encode("utf-8"))
                try:
                    doi = data_json_val.encode('utf-8')
                except Exception as e:
                    doi = ""
            if data_json_key == "fulljournalname":
                print(data_json_val.encode("utf-8"))
                try:
                    journal= data_json_val.encode('utf-8')
                except Exception as e:
                    journal = ""
            if data_json_key == "authors":
                for authors in data_json_val:
                    authors_list.append(authors['name'])
                authors_str_data = ' '.join(authors_list)
                print(authors_str_data)

            QzwResearchPapers_create = QzwResearchPapers.objects.create(
                research_paper_title=title,
                research_paper_doi=doi,
                research_paper_pdf_link="",
                research_paper_keywords=search_keyword,
                author_name=authors_str_data,
                journal_name=journal,
                search_source="Pubmed")

def get_offset_crawler_data(url_part_api,url_part,search_keyword):
    res = requests.get(url_part, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
    soup = BeautifulSoup(res.text, "html.parser", from_encoding="iso-8859-1")
    #get json content
    url_json_content = requests.get(url_part_api, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
    for range_tag in url_json_content['searchResults']:
        authors = []
        authors_str_data=""
        title = range_tag['title'].encode("utf-8")
        try:
            journal = range_tag['sourceTitle'].encode("utf-8")
        except Exception as j:
            journal =""
        try:
            doi = str(range_tag['doi'])
        except Exception as e:
            doi = ""
            #pass
        try:
            for authors_data in range_tag['authors']:
                authors.append(authors_data['name'])
            authors_str_data = ' '.join(authors)
        except Exception as a:
            authors=""

        QzwResearchPapers_create = QzwResearchPapers.objects.create(
            research_paper_title=title,
            research_paper_doi=doi,
            research_paper_keywords=search_keyword,
            author_name=authors_str_data,
            journal_name=journal)
    for range_tag2 in soup.find_all('li', {'class': 'next-link'}):
        for rangespantag in range_tag2.find_all('a'):
            if rangespantag.text == "next":
                print("in offset next exists and URL is -------------------")
                print(rangespantag.attrs['href'][7:])
                url_part_offset = 'https://www.sciencedirect.com/search' + rangespantag.attrs['href'][7:]
                url_part_api_offset = 'https://www.sciencedirect.com/search/api' + rangespantag.attrs['href'][7:]
                return get_offset_crawler_data(url_part_api_offset, url_part_offset,search_keyword)



# @api_view(['GET','POST'])
# # class runCommandList(request):
#
# def runCommandList(request):
#     commands = runCommands.objects.all()
#     serializer = runCommandSerializer(commands, many=True)
#     return Response(serializer.data)
#
# def post(self):
#         pass

class gromacsSample(APIView):

    def get(self, request):
        commands = gromacsSample.objects.all()
        serializer = runCommandSerializer(commands, many=True)
        return Response(serializer.data)

    def post(self):
        pass



def get_group_project_name(project_id):
    print("inside get get_group_project_name function")
    conn= connections['default'].cursor()
    sql_query = config.DB_QUERY['query_get_group_project_name'] % project_id
    print("sql_query is ")
    print(sql_query)
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    conn.execute(sql_query)
    print("conn is ")
    row = conn.fetchone()
    group_project_name = str(row[0])
    print("group_project_name is ",group_project_name)
    return group_project_name

def copy_function():
    with open(filesali) as user_file:
        with open(rename_name, "w") as new_user_file:
            for file_lines in user_file:
                print("printinh file lines")
                print(file_lines)

                new_user_file.write(file_lines)
    env = environ()
    # target is arg1 and template is arg2
    # a = automodel(env, alnfile='target-template.ali',
    #              knowns='template', sequence='target',
    #              assess_methods=(assess.DOPE,
    #                              #soap_protein_od.Scorer(),
    #                              assess.GA341))
    alnfile_alias = str(target) + '-' + str(template) + '.ali'
    print("printing alnfile_alias name in model_step2.py")
    print(alnfile_alias)
    a = automodel(env, alnfile=alnfile_alias,
                  knowns=str(template), sequence=str(target),
                  assess_methods=(assess.DOPE,
                                  # soap_protein_od.Scorer(),
                                  assess.GA341))
    a.starting_model = 1
    a.ending_model = int(ending_model_number)  # user input how many models user wants to generate
    a.make()
