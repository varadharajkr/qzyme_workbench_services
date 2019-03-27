# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import sys

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import request
from rest_framework import status
from .models import runCommands, gromacsSample , serverDetails ,commandDetails,QzwProjectDetails,QzwResearchPapers,ProjectToolEssentials
from .serializers import runCommandSerializer , serverrDetailsSerializer
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django import db
import subprocess
from subprocess import PIPE, Popen, call
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import shutil
import re
import config
import os
import ast
import glob
import urllib2
import json
import requests
import MySQLdb
from multiprocessing import Process
from urlparse import urljoin
from bs4 import BeautifulSoup

# Create your views ere.

# to run command in shell
def execute_command(command,inp_command_id):
    status_id = config.CONSTS['status_initiated']
    update_command_status(inp_command_id, status_id)
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    print "execute command"
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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        key_name_indexfile_input = 'mmpbsa_index_file_dict'

        ProjectToolEssentials_res_indexfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_indexfile_input).latest('entry_time')

        key_name_xtcfile_input = 'mmpbsa_md_xtc_file_list'

        ProjectToolEssentials_res_xtcfile_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_xtcfile_input).latest('entry_time')

        indexfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_indexfile_input.values)
        xtcfile_input_dict = list(ProjectToolEssentials_res_xtcfile_input.values)
        print type(indexfile_input_dict)
        print type(xtcfile_input_dict)
        # for xtc_file in xtcfile_input_dict:
        #     print xtc_file
        for indexfile_input in indexfile_input_dict:
            print indexfile_input

        return JsonResponse({"success": True})

        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
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
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})



class pathanalysis(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        #primary_command_runnable = re.sub('%input_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        #primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['shared_folder_path']+'Project/Project1/'+commandDetails_result.command_tool+'/'+config.PATH_CONFIG['distance_python_file'],primary_command_runnable)
        #primary_command_runnable = re.sub('%output_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print "process return code is "
        print process_return.returncode
        if process_return.returncode == 0:
            print "inside success"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            # moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
            # moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            # move_outputFiles(moveFile_source, moveFile_destination)
            # if commandDetails_result.command_title == 'Solvate':
            #     topolfile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/GmxtoPdb/outputFiles/topol.top'
            #     topolfile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            #     move_topolfile_(topolfile_source,topolfile_destination)
            update_command_status(inp_command_id,status_id)
            #move_files_(inp_command_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print "inside error"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            # moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
            # moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            # move_outputFiles(moveFile_source, moveFile_destination)
            #move_files_(inp_command_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#Extract Activation energy
class get_activation_energy(APIView):
    def get(self,request):
        pass

    def post(self,request):
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)
        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

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
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

class Hello_World(APIView):
    def get(self,request):
        pass
    def post(self,request):
        print ("Hello World")

        return JsonResponse({'success':True})


class mmpbsa(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

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
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})




class Contact_Score(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

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
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

def sol_group_option():
    print "=====================working directory in function is =============="
    print os.getcwd()
    log_file = "gromacs_solve_gro_indexing.txt"
    string_data = " SOL "
    matched_data = ""

    log_file_buffer = open(log_file, "r")

    for lines in log_file_buffer.readlines():
        # print "printing 1st loop"
        lines_data = lines
        if string_data in lines_data:
            matched_data = lines
            print matched_data
    SOL_option_value = matched_data
    SOL_option_value = SOL_option_value.split()
    print  SOL_option_value
    return SOL_option_value


@csrf_exempt
def md_simulation_preparation(project_id,project_name,command_tool,command_title):
    print "inside md_simulation_preparation function"
    key_name = 'md_simulation_no_of_runs'

    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = int(ProjectToolEssentials_res.values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print md_run_no_of_conformation

    source_file_path = config.PATH_CONFIG['shared_folder_path'] + str(project_name) + '/CatMec/MD_Simulation/'
    for i in range(int(md_run_no_of_conformation)):
        print (source_file_path + 'md_run' + str(i + 1))
        os.mkdir(source_file_path + 'md_run' + str(i + 1))
        dest_file_path = source_file_path + 'md_run' + str(i + 1)
        for file_name in os.listdir(source_file_path):
            try:
                print "inside try"
                shutil.copy(str(source_file_path) + file_name, dest_file_path)
            except IOError as e:
                print("Unable to copy file. %s" % e)
                pass
            except Exception:
                print("Unexpected error:", sys.exc_info())
                pass
        os.chdir(source_file_path + '/md_run' + str(i + 1))
        os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
        os.system("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
        os.system("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")
        os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")
        group_value = sol_group_option()
        SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
        SOL_replace_str = SOL_replace_backup
        SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value))
        print("printing group value in MD$$$$$$$$$$$$$$$$$$")
        print(group_value)
        print("printing after %SOL% replace")
        print(SOL_replace_str)
        os.system(SOL_replace_str)
        os.system("echo q | gmx make_ndx -f solve_ions.gro")
        os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
        os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")
        os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
        os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
        os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
        os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
        os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
        os.system(
            "gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
    return JsonResponse({'success': True})

#Substrate Parameterization
class Complex_Simulations(APIView):
    def get(self,request):
        pass


    def post(self,request):
        string_data = " SOL "
        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
        # ligand_name = QzwProjectEssentials_res.command_key
        # print "+++++++++++++++ligand name is++++++++++++"
        # print ligand_name


        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + '/CatMec/MD_Simulation/')
        print os.system("pwd")
        print os.getcwd()
        print "=========== title is =============="
        print commandDetails_result.command_title
        if commandDetails_result.command_title == "GromacsGenion":
            group_value = sol_group_option()
            ndx_file = "index.ndx"
            print config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/MD_Simulation/'
            dir_value = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/MD_Simulation/'
            os.system("rm "+dir_value+"/index.ndx")
            primary_command_runnable = re.sub('%SOL_value%',group_value,
                                              primary_command_runnable)
        if commandDetails_result.command_title == "md_run":
            md_simulation_preparation(project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title)
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
            print config.PATH_CONFIG[
                      'local_shared_folder_path'] + project_name + '/CatMec/MD_Simulation/'
            dir_value = config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + '/CatMec/MD_Simulation/'
            # os.system("rm "+dir_value+"/NEWPDB.PDB")

        print(primary_command_runnable)

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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
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
            print "inside success"
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": True,'output':result_crawlerdata_save,'process_returncode':result_crawlerdata_save})
        if result_crawlerdata_save == False:
            print "inside error"
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": False,'output':result_crawlerdata_save,'process_returncode':result_crawlerdata_save})


class MakeSubstitution(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        primary_command_runnable =re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/', primary_command_runnable)
        #primary_command_runnable = re.sub('%input_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        #primary_command_runnable = re.sub('%distance_python_file%',config.PATH_CONFIG['shared_folder_path']+'Project/Project1/'+commandDetails_result.command_tool+'/'+config.PATH_CONFIG['distance_python_file'],primary_command_runnable)
        #primary_command_runnable = re.sub('%output_folder_name%',config.PATH_CONFIG['shared_folder_path'],primary_command_runnable)
        print(primary_command_runnable)
        #serializer = SnippetSerializer(commandDetails_result, many=True)
        # command is (gmx pdb2gmx -f xyz.pdb -o xyz.gro -p topol.top -i xyz.itp -water spc -ff gromos43a1)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)

        shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool

        out, err = process_return.communicate()
        process_return.wait()
        print "process return code is "
        print process_return.returncode
        if process_return.returncode == 0:
            print "inside success"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            # moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
            # moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            # move_outputFiles(moveFile_source, moveFile_destination)
            # if commandDetails_result.command_title == 'Solvate':
            #     topolfile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/GmxtoPdb/outputFiles/topol.top'
            #     topolfile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            #     move_topolfile_(topolfile_source,topolfile_destination)
            update_command_status(inp_command_id,status_id)
            #move_files_(inp_command_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            print "inside error"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        primary_command_runnable = re.sub("%tconcoord_python_filepath%",config.PATH_CONFIG['local_shared_folder_path'] +  project_name + '/' + commandDetails_result.command_tool + '/Tconcoord.py',primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tcc/',primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/input3.cpf', primary_command_runnable)
        primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)

        print "runnable command is "
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool +'/')
        print "working directory is"
        print os.system("pwd")
        process_return = execute_command(primary_command_runnable,inp_command_id)
        process_return.wait()
        shared_folder_path = config.PATH_CONFIG['shared_folder_path']
        command_title_folder = commandDetails_result.command_title

        out, err = process_return.communicate()
        process_return.wait()
        print "process return code is "
        print process_return.returncode

        if process_return.returncode == 0:
            print "success executing command"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print "error executing command!!"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


class Homology_Modelling(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name

        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        primary_command_runnable = re.sub("%build_profile_python_file_path%", config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)

        primary_command_runnable = re.sub('%compare_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%align_2d_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%evaluate_model_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%model_single_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        editable_string = primary_command_runnable
        editable_string = editable_string.split()
        print"editable strign after split is"
        target = editable_string[2]
        print target
        template = editable_string[3]
        print template
        residue_no = editable_string[4]
        print residue_no
        ending_model_no = editable_string[5]
        print ending_model_no
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/')

        dirName = os.getcwd()
        print "dirname"
        print(os.getcwd())

        print "runnable command is"
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/')
        print "working directory after changing CHDIR"
        print(os.system("pwd"))
        # process_return = execute_command(primary_command_runnable)
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        print "execute command"
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print "printing status ofprocess"
        print process_return.returncode
        print "printing output of process"
        print out

        if process_return.returncode == 0:
            print "success executing command"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print "error executing command!!"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})
            

class Loop_Modelling(APIView):
    def get(self,request):
        pass

    def post(self,request):

        #get command details from database
        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name

        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        primary_command_runnable = re.sub("%build_profile_python_file_path%", config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)

        primary_command_runnable = re.sub('%compare_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%align_2d_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%evaluate_model_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%model_single_python_file_path%', config.PATH_CONFIG[
            'shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        editable_string = primary_command_runnable
        editable_string = editable_string.split()
        print"editable strign after split is"
        target = editable_string[2]
        print target
        template = editable_string[3]
        print template
        residue_no = editable_string[4]
        print residue_no
        ending_model_no = editable_string[5]
        print ending_model_no
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/')

        dirName = os.getcwd()
        print "dirname"
        print(os.getcwd())

        print "runnable command is"
        print(primary_command_runnable)
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/')
        print "working directory after changing CHDIR"
        print(os.system("pwd"))
        # process_return = execute_command(primary_command_runnable)
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        print "execute command"
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title = commandDetails_result.command_tool
        print "printing status ofprocess"
        print process_return.returncode
        print "printing output of process"
        print out

        if process_return.returncode == 0:
            print "success executing command"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print "error executing command!!"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            update_command_status(inp_command_id,status_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})


#ACTUAL WORKING AUTODOCK


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

class autodock(APIView):
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        print "tool before"
        print command_tool_title
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        key_name = 'enzyme_file'
        ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                               key_name=key_name).latest("entry_time")
        enzyme_file_name = ProjectToolEssentials_res.values
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        #shared_scripts
        primary_command_runnable = re.sub("pdb_to_pdbqt.py", config.PATH_CONFIG['shared_scripts'] +str(command_tool)+ "/pdb_to_pdbqt.py",primary_command_runnable)
        primary_command_runnable = re.sub("%python_sh_path%",config.PATH_CONFIG['python_sh_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%prepare_ligand4_py_path%",config.PATH_CONFIG['prepare_ligand4_py_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%add_python_file_path%",config.PATH_CONFIG['add_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%make_gpf_dpf_python_file_path%",config.PATH_CONFIG['make_gpf_dpf_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%grid_dock_map_python_file_path%",config.PATH_CONFIG['grid_dock_map_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%multiple_distance_python_file_path%",config.PATH_CONFIG['multiple_distance_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%multiple_angle_python_file_path%",config.PATH_CONFIG['multiple_angle_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%multiple_torsion_python_file_path%",config.PATH_CONFIG['multiple_torsion_python_file_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)

        #rplace string / paths for normal mode analysis
        primary_command_runnable = re.sub("%tconcoord_python_filepath%", config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/Tconcoord_no_threading.py',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tcc/',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/input3.cpf',
                                          primary_command_runnable)
        primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                          primary_command_runnable)
        #append mmtsb path to command for NMA
        primary_command_runnable = primary_command_runnable+" "+config.PATH_CONFIG['mmtsb_path']
        primary_command_runnable = primary_command_runnable +" " + enzyme_file_name
        print primary_command_runnable
        print "working directory before"
        print os.system("pwd")
        '''check for command tool
            split command tool
           if command tool == NMA (normal mode analysis)
                change DIR to NMA
            else
                change DIR to Autodock
        '''
        str_command_tool_title = str(command_tool_title)
        print type(str_command_tool_title)
        command_tool_title_split = str_command_tool_title.split('_')
        print "split is----------------------------"
        print type(command_tool_title_split)
        print command_tool_title_split
        if(command_tool_title_split[0] == "nma"):
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+command_tool_title_split[2]+'/')
        else:
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/')
        print "working directory after changing CHDIR"
        print os.system("pwd")
        # process PDB file format with PDBFIXER(MMTSB)
        if command_tool_title == "PdbtoPdbqt":
            #split primary_command_runnable and get PDB file as input to PDBFIXER
            primary_command_runnable_split = primary_command_runnable.split()
            print(config.PATH_CONFIG['mmtsb_path']+"/convpdb.pl "+primary_command_runnable_split[2]+" "+"-out generic > fixer_test.pdb")
            os.system(config.PATH_CONFIG['mmtsb_path']+"/convpdb.pl "+primary_command_runnable_split[2]+" "+"-out generic > fixer_test.pdb")
            print("mv fixer_test.pdb "+primary_command_runnable_split[2])
            os.system("mv fixer_test.pdb "+primary_command_runnable_split[2])
            print("primary_command_runnable %%%%%%%%%%%%%%%%%%%%%%%%%%%% ^^^^^^^^^^^^^^^^^^^")
            print(primary_command_runnable)
        #process_return = execute_command(primary_command_runnable)
        process_return = Popen(
            args=primary_command_runnable,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        print "execute command"
        print(primary_command_runnable)
        out, err = process_return.communicate()
        process_return.wait()
        # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

        command_title_folder = commandDetails_result.command_title
        command_tool_title= commandDetails_result.command_tool
        print "printing status ofprocess"
        print process_return.returncode
        print "printing output of process"
        print out

        if process_return.returncode == 0:
            print "output of out is"
            print out
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            fileobj.write(out)
            status_id = config.CONSTS['status_success']
            moveFile_source = config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/outputFiles/'
            moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            #move_outputFiles(moveFile_source,moveFile_destination)
            update_command_status(inp_command_id,status_id)
            #move_files_(inp_command_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
        if process_return.returncode != 0:
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
            #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            status_id = config.CONSTS['status_error']
            moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + commandDetails_result.command_title + '/outputFiles/'
            moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
            #move_outputFiles(moveFile_source, moveFile_destination)
            update_command_status(inp_command_id,status_id)
            #move_files_(inp_command_id)
            return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})

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
        #     process_grid_file(commandDetails_result,QzwProjectDetails_res,request)
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
    def get(self,request):
        pass

    def post(self,request):

        inp_command_id = request.POST.get("command_id")
        commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
        project_id = commandDetails_result.project_id
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        if command_tool_title == "Replace_Charge":
            print command_tool_title
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name

            primary_command_runnable = re.sub("%input_folder_name%", config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/Ligand_Parametrization/')
            print os.system("pwd")
            print os.getcwd()
            print "=========== title is =============="
            print commandDetails_result.command_title
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id)

            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print "process return code is "
            print process_return.returncode
            if process_return.returncode == 0:
                print "inside success"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print "inside error"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "Ligand_Parametrization":
            print command_tool_title
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name

            primary_command_runnable = re.sub("%input_folder_name%", config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/')
            print os.system("pwd")
            print os.getcwd()
            print "=========== title is =============="
            print commandDetails_result.command_title
            if commandDetails_result.command_title == "GromacsGenion":
                group_value = sol_group_option()
                ndx_file = "index.ndx"
                print config.PATH_CONFIG[
                          'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
                dir_value = config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
                os.system("rm " + dir_value + "/index.ndx")
                primary_command_runnable = re.sub('%SOL_value%', group_value,
                                                  primary_command_runnable)

            if commandDetails_result.command_title == "Parameterize":
                print config.PATH_CONFIG[
                          'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
                dir_value = config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'
                # os.system("rm "+dir_value+"/NEWPDB.PDB")

            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id)

            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print "process return code is "
            print process_return.returncode
            if process_return.returncode == 0:
                print "inside success"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print "inside error"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "get_make_complex_parameter_details" or command_tool_title == "make_complex_params" or command_tool_title == "md_run":
            print command_tool_title
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(project_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name

            primary_command_runnable = re.sub("%input_folder_name%", config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%input_output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_tool_title + '/',
                                              primary_command_runnable)
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + '/CatMec/MD_Simulation/')
            print (os.getcwd())
            if commandDetails_result.command_title == "md_run":
                primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
                md_simulation_preparation(project_id, project_name, commandDetails_result.command_tool,
                                          commandDetails_result.command_title)
            print("primary_command_runnable.........................................")
            print(primary_command_runnable)
            print ("execute_command(primary_command_runnable, inp_command_id).......")
            print (primary_command_runnable, inp_command_id)
            process_return = execute_command(primary_command_runnable, inp_command_id)

            command_title_folder = commandDetails_result.command_title

            out, err = process_return.communicate()
            process_return.wait()
            print "process return code is "
            print process_return.returncode
            if process_return.returncode == 0:
                print "inside success"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print "inside error"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})

        elif command_tool_title == "MD_Simulation":
            print command_tool_title
        elif command_tool_title == "Docking":
            print command_tool_title
            print "tool before"
            print command_tool_title
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            key_name = 'enzyme_file'
            ProjectToolEssentials_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                   key_name=key_name).latest("entry_time")
            enzyme_file_name = ProjectToolEssentials_res.values
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)

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
            primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
            primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                              primary_command_runnable)

            #rplace string / paths for normal mode analysis
            primary_command_runnable = re.sub("%tconcoord_python_filepath%", config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/Tconcoord_no_threading.py',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%tconcoord_additional_dirpath%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tcc/',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%tconcoord_input_filepath%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/input3.cpf',
                                              primary_command_runnable)
            primary_command_runnable = re.sub('%NMA_working_dir%', config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
                                              primary_command_runnable)
            #append mmtsb path to command for NMA
            primary_command_runnable = primary_command_runnable+" "+config.PATH_CONFIG['mmtsb_path']
            primary_command_runnable = primary_command_runnable+" "+enzyme_file_name
            print primary_command_runnable
            print "working directory before"
            print os.system("pwd")
            '''check for command tool
                split command tool
               if command tool == NMA (normal mode analysis)
                    change DIR to NMA
                else
                    change DIR to Autodock
            '''
            str_command_tool_title = str(command_tool_title)
            print type(str_command_tool_title)
            command_tool_title_split = str_command_tool_title.split('_')
            print "split is----------------------------"
            print type(command_tool_title_split)
            print command_tool_title_split
            if(command_tool_title_split[0] == "nma"):
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+command_tool_title_split[2]+'/')
            else:
                os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'+ commandDetails_result.command_title + '/')
            print "working directory after changing CHDIR"
            print os.system("pwd")
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
            print "execute command"
            out, err = process_return.communicate()
            process_return.wait()
            # shared_folder_path = config.PATH_CONFIG['shared_folder_path']

            command_title_folder = commandDetails_result.command_title
            command_tool_title= commandDetails_result.command_tool
            print "printing status ofprocess"
            print process_return.returncode
            print "printing output of process"
            print out

            if process_return.returncode == 0:
                print "output of out is"
                print out
                fileobj = open(config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_success']
                moveFile_source = config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/outputFiles/'
                moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
                #move_outputFiles(moveFile_source,moveFile_destination)
                update_command_status(inp_command_id,status_id)
                #move_files_(inp_command_id)
                return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
            if process_return.returncode != 0:
                fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
                #fileobj = open(shared_folder_path + 'Project/Project1/'+command_tool_title+'/'+ command_title_folder + '/logFiles/' + command_title_folder + '.log','w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                moveFile_source = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + commandDetails_result.command_title + '/outputFiles/'
                moveFile_destination = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/common_outputFiles/'
                #move_outputFiles(moveFile_source, moveFile_destination)
                update_command_status(inp_command_id,status_id)
                #move_files_(inp_command_id)
                return JsonResponse({"success": False,'output':err,'process_returncode':process_return.returncode})




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
    print "before return"
    return True
#alter dock.dpf file with respective .PDBQT file paths
def process_dock_file(commandDetails_result,QzwProjectDetails_res,request):
    print "in process dock file"
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
    print PDBQT_dir
    #read grid file
    for root, dirs, files in os.walk(PDBQT_dir):  # replace the . with your starting directory
        for file in files:
            if file.endswith(".pdbqt"):
                filelst = []
                dock_fileobj3 = open(config.PATH_CONFIG['local_shared_folder_path'] + QzwProjectDetails_res.project_name + '/' + commandDetails_result.command_tool + '/dock.dpf','r+')
                if file !=  ligand_file_name+'.pdbqt':
                    print "in HPMAE enzyme"
                    enzyme_file_name = file
                else:
                    pass
                for line in dock_fileobj3:
                    print "inside sinfle dockobj3"
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
    print "inside move outputfiles"
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
    QzwProjectDetails_res =QzwProjectDetails.objects.get(project_id=project_id)
    project_name = QzwProjectDetails_res.project_name
    source = config.PATH_CONFIG['local_qzw_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/'
    destination = config.PATH_CONFIG['local_shared_folder_path']+project_name+'/'+commandDetails_result.command_tool+'/'+commandDetails_result.command_title+'/'
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
                print path_file
                print destination
                #print shutil.copy(path_file, destination+"")
            #path_file = os.path.join(root, file)
            #print shutil.copy(path_file, destination)  # change you destination dir
            #print os.system("cp "+path_file+" "+destination)

def update_command_status(inp_command_id,status_id):
    print "updating command execution status"
    QzwProjectDetails_update_res = commandDetails.objects.filter(command_id=inp_command_id).update(status=status_id)
    print "result of update command execution status"
    print QzwProjectDetails_update_res
    return True

#process science direct data crawler
def get_crawler_data(start_offset,search_keyword):
    url = 'https://www.sciencedirect.com/search'+start_offset
    print "http URL is -"
    print url
    soup = BeautifulSoup(urlopen(url),"html.parser")
    for range_tag in soup.find_all('li', {'class': 'next-link'}):
        print "in first loop"
        for rangespantag in range_tag.find_all('a'):
            print "in second loop"
            if rangespantag.text == "next":
                get_next_page(rangespantag.attrs['href'])
                print "if next tag exists"
                data_class_variable =  {'class' : 'ResultItem'}
                data_attr_variable = soup.findAll(attrs=data_class_variable)

                for looping_data in data_attr_variable:
                    print "in looping data"
                    print "title is-"
                    print looping_data.h2.text.encode('utf-8').strip()
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
    print "in crawler initial fetch"
    base_url = 'https://www.sciencedirect.com/search'+base_page
    res = requests.get(base_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
    soup = BeautifulSoup(res.text,"html.parser",from_encoding="iso-8859-1")
    print "*******************pagination data is *********************"
    paginationsdata_list = soup.select('ol.Pagination > li')[0].get_text(strip=True)
    print paginationsdata_list
    page_offset_keyword = "Page1of"
    before_offset_keyword,page_offset_keyword,after_offset_keyword = paginationsdata_list.partition(page_offset_keyword)
    print "================  pagination count is ================================="
    print after_offset_keyword
    start_offset = 0
    for page_count in range(1,int(after_offset_keyword)):
        print "=============== page count is ======================="
        print page_count
        page_url = 'https://www.sciencedirect.com/search/api'+start_page+str(start_offset)
        print "================ page URL is ========================="
        print page_url
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
    print "in crawler google"
    for page_count in range(1, 990):
        print "=============== page count is ======================="
        print page_count
        page_url = 'https://scholar.google.co.in/scholar?start=' + str(page_count)+'&q='+encoded_search_keyword+'&hl=en&as_sdt=0,5'
        print "================ page URL is ========================="
        print page_url
        url_content = requests.get(page_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
        soup = BeautifulSoup(url_content.text, "html.parser", from_encoding="iso-8859-1")
        for range_tag in soup.findAll('div',{'class':'gs_r'}):
            try:
                title = range_tag.h3.get_text().encode('utf-8').strip()
            except Exception as e:
                title = ""
            print title
            print "================= anchor link is ================"
            try:
                paper_link = range_tag.h3.a['href'].encode('utf-8').strip()
            except Exception as a_href:
                paper_link= ""
            print "================= authors are ==================="
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
    print "in pubmed crawler"
    initial_page_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=&term="+str(encoded_search_keyword)
    print "---------------- initial page URL is --------------------"
    print initial_page_url
    url_content = requests.get(initial_page_url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
    print "-------------- json content is --------------------"
    print url_content
    #get total id_list count
    count_id_list = url_content['esearchresult']['count']
    print "------------- id count is --------------"
    print count_id_list
    #call API to get all ids list with total count if ids list
    page_url_count_all = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax="+str(count_id_list)+"&term=" + str(encoded_search_keyword)
    page_url_count_allcontent = requests.get(page_url_count_all, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()

    for id_s in page_url_count_allcontent['esearchresult']['idlist']:
        fetch_paper_details_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id=" + str(
            id_s)
        print "------------------ IDS URL is -----------------------"
        print fetch_paper_details_url
        paper_details_content = requests.get(fetch_paper_details_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}).json()
        for data_json_key, data_json_val in paper_details_content['result'][id_s].iteritems():
            authors_list =[]
            title = ""
            doi = ""
            journal= ""
            authors_str_data = ""
            if data_json_key == "title":
                print data_json_val.encode("utf-8")
                try:
                    title = data_json_val.encode('utf-8')
                except Exception as e:
                    title = ""
            if data_json_key == "elocationid":
                print data_json_val.encode("utf-8")
                try:
                    doi = data_json_val.encode('utf-8')
                except Exception as e:
                    doi = ""
            if data_json_key == "fulljournalname":
                print data_json_val.encode("utf-8")
                try:
                    journal= data_json_val.encode('utf-8')
                except Exception as e:
                    journal = ""
            if data_json_key == "authors":
                for authors in data_json_val:
                    authors_list.append(authors['name'])
                authors_str_data = ' '.join(authors_list)
                print authors_str_data

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
                print "in offset next exists and URL is -------------------"
                print rangespantag.attrs['href'][7:]
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

def copy_function():
    with open(filesali) as user_file:
        with open(rename_name, "w") as new_user_file:
            for file_lines in user_file:
                print "printinh file lines"
                print file_lines

                new_user_file.write(file_lines)
    env = environ()
    # target is arg1 and template is arg2
    # a = automodel(env, alnfile='target-template.ali',
    #              knowns='template', sequence='target',
    #              assess_methods=(assess.DOPE,
    #                              #soap_protein_od.Scorer(),
    #                              assess.GA341))
    alnfile_alias = str(target) + '-' + str(template) + '.ali'
    print "printing alnfile_alias name in model_step2.py"
    print alnfile_alias
    a = automodel(env, alnfile=alnfile_alias,
                  knowns=str(template), sequence=str(target),
                  assess_methods=(assess.DOPE,
                                  # soap_protein_od.Scorer(),
                                  assess.GA341))
    a.starting_model = 1
    a.ending_model = int(ending_model_number)  # user input how many models user wants to generate
    a.make()
