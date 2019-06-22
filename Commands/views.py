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


def execute_command_md_run(command):
    process =Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True
    )
    print "execute command md run"
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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)


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
        md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.values.replace('\\', '/')

        # get .ndx file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_ndx_file = 'mmpbsa_index_file'

        ProjectToolEssentials_res_ndx_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ndx_file).latest('entry_time')
        md_simulations_ndx_file = ProjectToolEssentials_res_ndx_file_input.values.replace('\\', '/')

        key_name_CatMec_input = 'substrate_input'
        command_tootl_title = "CatMec"
        # get list of ligand inputs
        ProjectToolEssentials_res_CatMec_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                       key_name=key_name_CatMec_input).latest('entry_time')
        CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.values)
        # if User has only one ligand as input
        multiple_ligand_input = False
        if len(CatMec_input_dict) > 1:
            multiple_ligand_input = True

        indexfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_indexfile_input.values)
        xtcfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_xtcfile_input.values)

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
            md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + \
                                config.PATH_CONFIG['md_simulations_path'] + xtcfile_inputvalue_formatted + " "
        gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
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
            #for multiple ligand input
            print "for multiple ligand input"
            #get user input ligand name from DB
            key_name_ligand_input = 'mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.values
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
            print reversed_indexfile_complex_option_input
            print reversed_indexfile_receptor_option_input
            maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
            protien_ligand_complex_index = receptor_index + 1
            #write protien ligand complex index number to DB
            entry_time = datetime.now()
            key_name_protien_ligand_complex_index = 'mmpbsa_index_file_protien_ligand_complex_number'
            ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(tool_title=commandDetails_result.command_tool,
                                                                                      project_id=project_id,
                                                                                      key_name=key_name_protien_ligand_complex_index,
                                                                                      values=protien_ligand_complex_index,
                                                                                      entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            ligand_name_index = protien_ligand_complex_index + 1
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                               'md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(
                str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(reversed_indexfile_complex_option_input) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n"+str(ligand_name_input)+"\nname "+str(ligand_name_index)+" ligand"+ "\nq\n")
            file_gmx_make_ndx_input.close()

            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                               'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + "gmx_make_ndx_input.txt"

            print " make index command"
            print gmx_make_ndx
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
                values=protien_ligand_complex_index,
                entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                              'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                              'md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(str(protein_index)+"\nname "+str(receptor_index)+" receptor\n"+str(protein_index)+" | "+str(ligandname_index)+"\nname "+str(protien_ligand_complex_index)+" complex"+"\n" +str(ligandname_index)+"\nname "+str(ligand_name_index)+" ligand"+"\nq\n")
            file_gmx_make_ndx_input.close()
            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                               'mmpbsa_project_path'] + "complex_index.ndx <"+config.PATH_CONFIG[
                                              'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                              'md_simulations_path'] + "gmx_make_ndx_input.txt"

            print " make index command"
            print gmx_make_ndx
            os.system(gmx_make_ndx)

        perform_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file)
        #===================   post processing after make index  ===============================
        # copy MD .tpr file to MMPBSA working directory
        source_tpr_md_file = config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                 'md_simulations_path'] + md_simulations_tpr_file
        tpr_file_split = md_simulations_tpr_file.split("/")
        dest_tpr_md_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                           config.PATH_CONFIG['mmpbsa_project_path'] + tpr_file_split[1]

        shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

        # copy topology file from MS to MMPBSA working directory
        source_topology_file = config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                   'md_simulations_path'] + tpr_file_split[0] + "/topol.top"
        dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                             config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top"
        shutil.copyfile(source_topology_file, dest_topology_file)

        # copy ligand .itp files
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            source_itp_file = config.PATH_CONFIG[
                                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                  'md_simulations_path'] + tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
            dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path'] + ligand_name_split[0] + ".itp"
            shutil.copyfile(source_itp_file, dest_itp_file)

        #copy atom_types.itp file from MD dir
        source_atomtype_itp_file = config.PATH_CONFIG[
                              'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                              'md_simulations_path'] + tpr_file_split[0] + "/" + "atomtypes" + ".itp"
        dest_atomtype_itp_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "atomtypes" + ".itp"
        shutil.copyfile(source_atomtype_itp_file, dest_atomtype_itp_file)

        key_name_ligand_input = 'mmpbsa_input_ligand'
        # processing itp files
        pre_process_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input)

        # ----------------------   make a "trail" directory for MMPBSA   -----------------------
        os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                  config.PATH_CONFIG['mmpbsa_project_path'] + "trial")
        # copying MMPBSA input files to trail directory
        # copy .XTC file
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "merged-recentered.xtc",
                        config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                        config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.xtc")

        # copy other input files for MMPBSA
        for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path']):
            # copy .TPR file
            if file_name.endswith(".tpr"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.tpr")
            # copy .NDX file
            if file_name.endswith(".ndx"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/index.ndx")

            # copy .TOP file
            if file_name.endswith(".top"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
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
                    ligand_name = ProjectToolEssentials_res_ligand_input.values
                else:
                    #for single ligand
                    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
                        ligand_name = ligand_inputvalue.split("_")[0]
                if file_name[:-4] == ligand_name:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/ligand.itp")
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/"+file_name)
                else:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)

        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                                    config.PATH_CONFIG['mmpbsa_project_path'])
        os.system("sh "+config.PATH_CONFIG['GMX_run_file_one'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
        os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])

        #update command status to database
        try:
            print "<<<<<<<<<<<<<<<<<<<<<<< error try block CatMec MMPBSA >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
        except db.OperationalError as e:
            print "<<<<<<<<<<<<<<<<<<<<<<< error except block CatMec MMPBSA   >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            db.close_old_connections()
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
        return JsonResponse({"success": True})




#new code for Designer MMPBSA
def designer_queue_analyse_mmpbsa(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    entry_time = datetime.now()
    # get command details from database
    #create ANALYSIS and MMPBSA folder in Mutations respective folder
    os.system("mkdir "+config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" +command_tool + "/" +md_mutation_folder+"/Analysis")
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/Analysis/MMPBSA/")
    inp_command_id = request.POST.get("command_id")
    commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
    project_id = commandDetails_result.project_id
    QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
    project_name = QzwProjectDetails_res.project_name

    mdsimulations_source = config.PATH_CONFIG['shared_folder_path'
                           ] +  project_name + '/' + command_tool + "/"+md_mutation_folder +"/"
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
                        print "xtc file found"  # ^\[.*\]\n
                        xtc_files_list.update({xtc_file_list_count: os.path.join(dirs, dir_files)})
                        xtc_file_list_count += 1

    ndx_count = 0
    ndx_input_dict = {}
    #
    print tpr_file_list
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
                                                                                values=tpr_file_list[0],
                                                                                entry_time=entry_time)
    result_ProjectToolEssentials_save_mmpbsa_tpr_file = ProjectToolEssentials_save_designer_mmpbsa_tpr_file.save()

    key_name_CatMec_input = 'substrate_input'
    command_tootl_title = "CatMec"
    # get list of ligand inputs
    ProjectToolEssentials_res_CatMec_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                   key_name=key_name_CatMec_input).latest('entry_time')
    CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.values)
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
        md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + \
                            command_tool + "/" + md_mutation_folder+ "/" + xtcfile_inputvalue_formatted + " "
    gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" +command_tool + "/" +md_mutation_folder+"/"+ config.PATH_CONFIG[
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
        # for multiple ligand input
        print "for multiple ligand input"
        # get user input ligand name from DB
        key_name_ligand_input = 'mmpbsa_input_ligand'

        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.values
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
        print reversed_indexfile_complex_option_input
        print reversed_indexfile_receptor_option_input
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
            values=protien_ligand_complex_index,
            entry_time=entry_time)
        result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
        ligand_name_index = protien_ligand_complex_index + 1
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] + project_name + '/' + command_tool+"/"+md_mutation_folder +"/"+ "gmx_make_ndx_input.txt", "w")
        file_gmx_make_ndx_input.write(
            str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(
                reversed_indexfile_complex_option_input) + "\nname " + str(
                protien_ligand_complex_index) + " complex" + "\n" + str(ligand_name_input) + "\nname " + str(
                ligand_name_index) + " ligand" + "\nq\n")
        file_gmx_make_ndx_input.close()

        gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -n " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + '/' + md_mutation_folder + "/" + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + "/" + md_mutation_folder + '/' + \
                       config.PATH_CONFIG[
                           'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_make_ndx_input.txt"

        print " make index command"
        print gmx_make_ndx
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
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] + project_name + '/' + command_tool+"/"+md_mutation_folder +"/"+ "gmx_make_ndx_input.txt", "w")
        file_gmx_make_ndx_input.write(
            str(protein_index) + "\nname " + str(receptor_index) + " receptor\n" + str(protein_index) + " | " + str(
                ligandname_index) + "\nname " + str(protien_ligand_complex_index) + " complex"+ "\nq\n")
        file_gmx_make_ndx_input.close()
        gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -n " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + '/' + md_mutation_folder + "/" + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + "/" + md_mutation_folder + '/' + \
                       config.PATH_CONFIG[
                           'mmpbsa_project_path'] + "index.ndx < " + config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_make_ndx_input.txt"


        print " make index command"
        print gmx_make_ndx
        os.system(gmx_make_ndx)

    perform_cmd_trajconv_designer_queue(project_name, project_id, md_simulations_tpr_file, md_simulations_ndx_file,md_mutation_folder,command_tool)
    # ===================   post processing after make index  ===============================
    # copy MD .tpr file to MMPBSA working directory
    source_tpr_md_file = config.PATH_CONFIG[
                             'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" + md_simulations_tpr_file
    tpr_file_split = md_simulations_tpr_file.split("/")
    dest_tpr_md_file = config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
                       config.PATH_CONFIG['mmpbsa_project_path'] + tpr_file_split[1]

    shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

    # copy topology file from MS to MMPBSA working directory
    source_topology_file = config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +  tpr_file_split[0] + "/topol.top"
    dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ config.PATH_CONFIG['mmpbsa_project_path'] + "topol.top"
    shutil.copyfile(source_topology_file, dest_topology_file)

    # copy ligand .itp files
    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
        ligand_name_split = ligand_inputvalue.split("_")
        source_itp_file = config.PATH_CONFIG[
                              'local_shared_folder_path'] + project_name + '/' +command_tool+"/"+md_mutation_folder+"/"+ tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
        dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path'] + ligand_name_split[0] + ".itp"
        shutil.copyfile(source_itp_file, dest_itp_file)

    key_name_ligand_input = 'mmpbsa_input_ligand'
    # processing itp files
    pre_process_designer_queue_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input,md_mutation_folder,command_tool)

    # ----------------------   make a "trail" directory for MMPBSA   -----------------------
    os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path'] + "trial")
    # copying MMPBSA input files to trail directory
    # copy .XTC file
    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                    config.PATH_CONFIG['mmpbsa_project_path'] + "merged-recentered.xtc",
                    config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                    config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.xtc")

    # copy other input files for MMPBSA
    for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path']):
        # copy .TPR file
        if file_name.endswith(".tpr"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/npt.tpr")
        # copy .NDX file
        if file_name.endswith(".ndx"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/index.ndx")

        # copy .TOP file
        if file_name.endswith(".top"):
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                            config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                            config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)
        # copy .ITP files
        if file_name.endswith(".itp"):
            # renaming user input ligand as LIGAND
            key_name_ligand_input = 'mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.values
            if file_name[:-4] == ligand_name:
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+\
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/ligand.itp")
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)
            else:
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+ \
                                config.PATH_CONFIG['mmpbsa_project_path'] + "trial/" + file_name)

    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + \
             config.PATH_CONFIG['mmpbsa_project_path'])
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_one'])
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])
    return JsonResponse({"success": True})

def hotspot_analyse_mmpbsa(request,mutation_dir_mmpbsa, project_name, command_tool,project_id, user_id):
    #MMPBSA for hotspot module
    entry_time = datetime.now()
    # get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "hotspot_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    hotspot_mutations_file = ProjectToolEssentials_mutations_file.values

    #create MMPBSA dir only
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/")

    # -----------------------------------------------------------------------------------------------------
    # --------------------    get TRJCAT command string to be executed    ---------------------------------
    # -----------------------------------------------------------------------------------------------------

    trajcat_return_list = get_hotspot_trjcat_command_str(request,mutation_dir_mmpbsa,  project_name, command_tool, project_id, user_id)

    # return list of values (0 - gro files str, 1 - tpr file str, 2 - index file str, 3 - topology file)
    # [em_gro_file_str, em_tpr_file_str, md_index_file_str,md_topology_file_str]
    # -----------------------------------------------------------------------------------------------------
    # --------------------    TRJCAT RUN   ----------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------

    gmx_trjcat_cmd = "gmx trjcat -f " + trajcat_return_list[0] + " -o " + config.PATH_CONFIG[
       'local_shared_folder_path'] + project_name + "/" +command_tool + "/" +mutation_dir_mmpbsa+"/MMPBSA/"+ "merged.xtc -keeplast -cat"

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
    CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.values)
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
        print "for multiple ligand input"
        # get user input ligand name from DB
        key_name_ligand_input = 'mmpbsa_input_ligand'

        ProjectToolEssentials_res_ligand_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ligand_input).latest('entry_time')
        ligand_name = ProjectToolEssentials_res_ligand_input.values
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
        print reversed_indexfile_complex_option_input
        print reversed_indexfile_receptor_option_input
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
                                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt",
                                       "w")
        file_gmx_make_ndx_input.write(
            str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(
                reversed_indexfile_complex_option_input) + "\nname " + str(
                protien_ligand_complex_index) + " complex" + "\n" + str(ligand_name_input) + "\nname " + str(
                ligand_name_index) + " ligand" + "\nq\n")
        file_gmx_make_ndx_input.close()

        gmx_make_ndx = "gmx make_ndx -f " + md_simulations_tpr_file + " -n " + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + "/" + mutation_dir_mmpbsa + '/MMPBSA/' + "index.ndx < " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt"

        print " make index command in HOTSPOT MMPBSA"
        print gmx_make_ndx
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
        file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt",
                                       "w")
        file_gmx_make_ndx_input.write(
            str(protein_index) + "\nname " + str(receptor_index) + " receptor\n" + str(protein_index) + " | " + str(
                ligandname_index) + "\nname " + str(protien_ligand_complex_index) + " complex")
        file_gmx_make_ndx_input.close()
        gmx_make_ndx = "gmx make_ndx -f " + md_simulations_tpr_file + " -n " + md_simulations_ndx_file + " -o " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + command_tool + "/" + mutation_dir_mmpbsa + '/MMPBSA/' + "index.ndx < " + \
                       config.PATH_CONFIG[
                           'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_make_ndx_input.txt"

        print " make index command in HOTSPOT MMPBSA"
        print gmx_make_ndx
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
                           'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + tpr_file_split[-1]

    shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

    # ------------------   copy topology file from MS to MMPBSA working directory   ------------------------------------
    source_topology_file = trajcat_return_list[3] # topology file
    dest_topology_file = config.PATH_CONFIG[
                             'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "topol.top"
    shutil.copyfile(source_topology_file, dest_topology_file)

    # ------------------   copy ligand .itp files   --------------------------------------------------------------------
    for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
        ligand_name_split = ligand_inputvalue.split("_")
        # rsplit is a shorthand for "reverse split", and unlike regular split works from the end of a string.
        source_itp_file = md_simulations_tpr_file.rsplit("/",1)[0] + "/" + ligand_name_split[0] + ".itp"
        dest_itp_file = config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + ligand_name_split[0] + ".itp"
        shutil.copyfile(source_itp_file, dest_itp_file)

    key_name_ligand_input = 'mmpbsa_input_ligand'
    # processing itp files
    pre_process_hotspot_mmpbsa_imput(project_id, project_name, md_simulations_tpr_file, CatMec_input_dict,
                                            key_name_ligand_input, mutation_dir_mmpbsa, command_tool)

    # ----------------------   make a "trail" directory for MMPBSA   -----------------------
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial")

    # -----------------   copying MMPBSA input files to trail directory   ----------------------------------------------
    # -----------------   copy .XTC file   -----------------------------------------------------------------------------
    shutil.copyfile(config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged-recentered.xtc",
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/npt.xtc")

    # -----------   copy other input files for MMPBSA   ----------------------------------------------------------------
    for file_name in os.listdir(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" ):
        # -------------   copy .TPR file   -----------------------------------------------------------------------------
        if file_name.endswith(".tpr"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/npt.tpr")
        # -------------   copy .NDX file   -----------------------------------------------------------------------------
        if file_name.endswith(".ndx"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/index.ndx")

        # -------------   copy .TOP file   -----------------------------------------------------------------------------
        if file_name.endswith(".top"):
            shutil.copyfile(config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                            config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)
        # -------------   copy .ITP files   ----------------------------------------------------------------------------
        if file_name.endswith(".itp"):
            # renaming user input ligand as LIGAND
            key_name_ligand_input = 'mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.values
            if file_name[:-4] == ligand_name:
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/ligand.itp")
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)
            else:
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + file_name,
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "trial/" + file_name)

    os.chdir(config.PATH_CONFIG[
                 'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" )
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_one'])
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_two'])
    os.system("sh " + config.PATH_CONFIG['GMX_run_file_three'])
    return JsonResponse({"success": True})


#trajcat for Hotspot MMPBSA module
def get_hotspot_trjcat_command_str(request,mutation_dir_mmpbsa,  project_name, command_tool, project_id, user_id):
    em_gro_file_str = ""
    em_tpr_file_str = ""
    md_index_file_str = ""
    md_topology_file_str = ""
    variant_index_dir = 0  # variant dirs counter
    for mutations_dirs in os.listdir(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                     + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa):
        # ---------- loop for variant dirs ---------------
        if os.path.isdir(os.path.join(config.PATH_CONFIG[
                                          'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' +mutation_dir_mmpbsa,
                                      mutations_dirs)):
            # ------------ loop for mutations dir -----------------
            pdb_file_index_str = 0  # index for PDB (file) variant
            for variants_dir in os.listdir(config.PATH_CONFIG[
                                               'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa + "/" + mutations_dirs + "/"):
                # <<<<<<<<<<<<<< loop for variants dir >>>>>>>>>>>>>>>>>
                for md_run_dir in os.listdir(config.PATH_CONFIG[
                                                   'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/" +variants_dir+"/md_run0/"):
                    #filter for em.gro file
                    if md_run_dir.strip() == "em.gro":
                        em_gro_file_str += config.PATH_CONFIG[
                                                   'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/" +variants_dir+"/md_run0/" + md_run_dir.strip() + " "

                    # filter for em.tpr file
                    if md_run_dir.strip() == "em.tpr":
                        em_tpr_file_str = str(config.PATH_CONFIG[
                                                   'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/" +variants_dir+"/md_run0/" + md_run_dir.strip())

                    # filter for index file
                    if md_run_dir.strip() == "index.ndx":
                        md_index_file_str = str(config.PATH_CONFIG[
                                                   'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa +"/" +variants_dir+"/md_run0/" + md_run_dir.strip())

                    # filter for topology file
                    if md_run_dir.strip() == "topol.top":
                        md_topology_file_str = str(config.PATH_CONFIG[
                                                    'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + mutation_dir_mmpbsa + "/" + variants_dir + "/md_run0/" + md_run_dir.strip())

                pdb_file_index_str += 1
    variant_index_dir += 1
    # return list of values (0 - gro files str, 1 - tpr file str, 2 - index file str)
    return [em_gro_file_str,em_tpr_file_str,md_index_file_str,md_topology_file_str]

def perform_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file):
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
                                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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

    os.system("gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
              config.PATH_CONFIG['mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'md_simulations_path'] + "gmx_trjconv_input.txt")

def perform_cmd_trajconv_designer_queue(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file,md_mutation_folder,command_tool):
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
                                      'local_shared_folder_path'] + project_name + '/' +command_tool+"/" +md_mutation_folder+"/"+"gmx_trjconv_input.txt", "w")
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

    os.system("gmx trjconv -f " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + command_tool + "/" + md_mutation_folder + "/" + config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/" +
              config.PATH_CONFIG[
                  'mmpbsa_project_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + md_simulations_ndx_file + " < " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + md_mutation_folder + "/" + "gmx_trjconv_input.txt")



def perform_cmd_trajconv_hotspot_mmpbsa(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file,mutation_dir_mmpbsa,command_tool):
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
                                      'local_shared_folder_path'] + project_name + '/' +command_tool+"/" +mutation_dir_mmpbsa+"/"+"gmx_trjconv_input.txt", "w")
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

    os.system("gmx trjconv -f " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged.xtc -s " + md_simulations_tpr_file + " -pbc mol -ur compact -o " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + mutation_dir_mmpbsa + "/MMPBSA/" + "merged-recentered.xtc -center -n " + md_simulations_ndx_file + " < " +
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + command_tool + "/" + mutation_dir_mmpbsa + "/" + "gmx_trjconv_input.txt")


def pre_process_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input):

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                          'md_simulations_path'] +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ pairs ]':
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            print "adding topology file contents are"
            print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+ "complex.itp", "w") as new_topology_file:
                new_topology_file.write(topology_initial_content + "\n" +
                                        topology_content_atoms + topology_file_atoms_content + "\n" +
                                        topology_content_bonds + topology_file_bonds_content + "\n" +
                                        topology_content_pairs + topology_file_pairs_content + "\n" +
                                        topology_content_angles + topology_file_angles_content + "\n" +
                                        topology_content_dihedrals + topology_file_dihedrals_content)

            atoms_final_count = atoms_lastcount
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+"new_" +ligand_inputvalue.split("_")[0]+".itp", "w") as new_itp_file:
                new_itp_file.write(initial_text_content)

    #--------------------   update INPUT.dat file ---------------------------------
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
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/CatMec/' + \
                            config.PATH_CONFIG['mmpbsa_project_path']+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)

#designer queue
def pre_process_designer_queue_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input,md_mutation_folder,command_tool):

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] + project_name + '/'+command_tool+"/" +md_mutation_folder+"/"+tpr_file_split[0]+"/topol.top") as topol_file:
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
                          'local_shared_folder_path'] + project_name + '/' +command_tool+"/"+md_mutation_folder+"/"+ tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
                          'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/" +tpr_file_split[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ pairs ]':
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "topol.top", "r+") as topology_bak_file:
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
            print "adding topology file contents are"
            print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+ "complex.itp", "w") as new_topology_file:
                new_topology_file.write(topology_initial_content + "\n" +
                                        topology_content_atoms + topology_file_atoms_content + "\n" +
                                        topology_content_bonds + topology_file_bonds_content + "\n" +
                                        topology_content_pairs + topology_file_pairs_content + "\n" +
                                        topology_content_angles + topology_file_angles_content + "\n" +
                                        topology_content_dihedrals + topology_file_dihedrals_content)

            atoms_final_count = atoms_lastcount
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+"new_" +ligand_inputvalue.split("_")[0]+".itp", "w") as new_itp_file:
                new_itp_file.write(initial_text_content)

    #--------------------   update INPUT.dat file ---------------------------------
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
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG['mmpbsa_project_path']+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)


#process hotspot mmpbsa inputs
def pre_process_hotspot_mmpbsa_imput(project_id, project_name, md_simulations_tpr_file, CatMec_input_dict,
                                            key_name_ligand_input, mutation_dir_mmpbsa, command_tool):

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.values
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
            with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(md_simulations_tpr_file.rsplit("/",1)[0]+"/"+ ligand_inputvalue.split("_")[0]+".itp", "r+") as itp_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ pairs ]':
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "topol.top", "r+") as topology_bak_file:
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
            print "adding topology file contents are"
            print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+ "complex.itp", "w") as new_topology_file:
                new_topology_file.write(topology_initial_content + "\n" +
                                        topology_content_atoms + topology_file_atoms_content + "\n" +
                                        topology_content_bonds + topology_file_bonds_content + "\n" +
                                        topology_content_pairs + topology_file_pairs_content + "\n" +
                                        topology_content_angles + topology_file_angles_content + "\n" +
                                        topology_content_dihedrals + topology_file_dihedrals_content)

            atoms_final_count = atoms_lastcount
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + "/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+"new_" +ligand_inputvalue.split("_")[0]+".itp", "w") as new_itp_file:
                new_itp_file.write(initial_text_content)

    #--------------------   update INPUT.dat file ---------------------------------
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
            else:
                new_input_lines += line

    with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name +"/"+command_tool+"/"+mutation_dir_mmpbsa+"/MMPBSA/"+"INPUT.dat", "w") as mmpbsa_input_file_update:
        mmpbsa_input_file_update.write(new_input_lines)

#Designer trajconv
def perform__designer_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file):
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
                                      'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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

    os.system("gmx trjconv -f " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
              config.PATH_CONFIG['designer_mmpbsa_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + md_simulations_tpr_file + " -pbc mol -ur compact -o " + \
              config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/Designer/' + config.PATH_CONFIG[
                  'designer_mmpbsa_path'] + "merged-recentered.xtc -center -n " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + md_simulations_ndx_file + " < " + config.PATH_CONFIG[
                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                  'designer_md_simulations_path'] + "gmx_trjconv_input.txt")

#designer module process mmpbsa input file
def pre_process_designer_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input):

    #=======================  get user input ligand  ============================
    ProjectToolEssentials_res_ligand_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_ligand_input).latest('entry_time')
    ligand_name = ProjectToolEssentials_res_ligand_input.values
    #======================= End of get user input ligand  ======================


    #==================  get [ ATOMS ] section final atom count  =================
    count_line = 0
    line_list = []
    with open(config.PATH_CONFIG[
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
                          'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "topol.top", "r+") as topology_bak_file:
                for line2 in topology_bak_file:
                    if line2.strip() == '[ pairs ]':
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
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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
            print "adding topology file contents are"
            print topology_initial_content + "\n" + topology_content_atoms + topology_file_atoms_content + "\n"
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+ "complex.itp", "w") as new_topology_file:
                new_topology_file.write(topology_initial_content + "\n" +
                                        topology_content_atoms + topology_file_atoms_content + "\n" +
                                        topology_content_bonds + topology_file_bonds_content + "\n" +
                                        topology_content_pairs + topology_file_pairs_content + "\n" +
                                        topology_content_angles + topology_file_angles_content + "\n" +
                                        topology_content_dihedrals + topology_file_dihedrals_content)

            atoms_final_count = atoms_lastcount
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path']+"new_" +ligand_inputvalue.split("_")[0]+".itp", "w") as new_itp_file:
                new_itp_file.write(initial_text_content)

    #--------------------   update INPUT.dat file ---------------------------------
    new_input_lines = ""
    itp_ligand = "ligand.itp"
    itp_receptor = "complex.itp"
    with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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

    with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name

        # Path analysis for CatMec and Designer modules
        # Check for Command Title
        if commandDetails_result.command_title == "CatMec":
            # Execute for CatMec module
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            # change working directory
            try:
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
            except:  # except path error
                # create directory
                os.system("mkdir " + config.PATH_CONFIG[
                    'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                # change directory
                os.chdir(config.PATH_CONFIG[
                             'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)

            #copy PDB frames from CatMec Analysis Contact Score module
            #catmec contact score path
            catmec_contact_score_path = config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/Contact_Score/'
            for dir_files in listdir(catmec_contact_score_path):
                if dir_files.endswith(".pdb"):  # applying .tpr file filter
                    shutil.copyfile(catmec_contact_score_path+dir_files,config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool+"/"+dir_files)

            #copy execution files (scripts)
            for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
                shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'+script_dir_file,config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool+"/"+script_dir_file)

            # execute PathAnalysis command
            process_return = execute_command(primary_command_runnable, inp_command_id)
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                print JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
                print JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})

        else:
            # Execute for Designer module Path Analysis
            #update command status to initiated
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)

            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + 'Designer' + '/mutated_list.txt', 'r') as fp_mutated_list:
                mutated_list_lines = fp_mutated_list.readlines()
                variant_index_count = 0
                for line_mutant in mutated_list_lines:
                    # line_mutant ad mutation folder
                    primary_command_runnable = commandDetails_result.primary_command
                    # change working directory
                    try:
                        os.chdir(config.PATH_CONFIG[
                                     'local_shared_folder_path'] + project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                    except OSError as e:  # excep path error
                        error_num, error_msg = e
                        if error_msg.strip() == "The system cannot find the file specified":
                            # create directory
                            os.system("mkdir " + config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                            # change directory
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] + project_name + '/'+'Designer/'+line_mutant+'/' +'/Analysis/' +'Path_Analysis/')
                    # IN LOOP
                    # copy PDB frames from Designer Analysis Contact Score module
                    # contact score path
                    designer_queue_contact_score_path = config.PATH_CONFIG[
                                                            'local_shared_folder_path'] + project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Contact_Score/'
                    for dir_files in listdir(designer_queue_contact_score_path):
                        if dir_files.endswith(".pdb"):
                            shutil.copyfile(designer_queue_contact_score_path + dir_files, config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Path_Analysis/' + dir_files)

                    # copy execution files (scripts)
                    for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
                        shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/' + script_dir_file,
                                        config.PATH_CONFIG[
                                            'local_shared_folder_path'] + project_name + '/' + 'Designer' + '/' + line_mutant + '/Analysis/Path_Analysis/' + script_dir_file)

                    # run Path analysis last executed command(executed in CatMec module)
                    os.system(commandDetails_result.primary_command)

#designer queue  path analysis
def designer_queue_path_analysis(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    commandDetails_result = commandDetails.objects.get(project_id=project_id,user_id=user_id,command_tool='Path_Analysis',command_title='CatMec').latest('entry_time')
    try:
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
    except OSError as e:  # except path error
        error_num, error_msg = e
        if error_msg.strip() == "The system cannot find the file specified":
            # create directory
            os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
            # change directory
            os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/')
    # copy PDB frames from Designer Analysis Contact Score module
    # contact score path
    designer_queue_contact_score_path = config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Contact_Score/'
    for dir_files in listdir(designer_queue_contact_score_path):
        if dir_files.endswith(".pdb"):
            shutil.copyfile(designer_queue_contact_score_path + dir_files, config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/'+ dir_files)

    # copy execution files (scripts)
    for script_dir_file in listdir(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/'):
        shutil.copyfile(config.PATH_CONFIG['shared_scripts'] + 'Path_Analysis/' + script_dir_file, config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + md_mutation_folder + '/Analysis/Path_Analysis/'+ script_dir_file)

    #run Path analysis last executed command(executed in CatMec module)
    os.system(commandDetails_result.primary_command)


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

        print('before replacing primary_command_runnable')
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
        inp_command_id = 2599
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)
        time.sleep(3)
        try:
            django_logger.info("Hey there it works!! and in post is"+str(request.POST)+"\nend of post data")
            django_logger.debug("Hey there it works!! and in post is" + str(request.POST) + "\nend of post data")
            print "<<<<<<<<<<<<<<<<<<<<<<< in try >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            print "project name after sleep is "
            print project_name
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
            return JsonResponse({'success': True})
        except db.OperationalError as e:
            print "<<<<<<<<<<<<<<<<<<<<<<< in except >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            db.close_old_connections()
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            print "project name after sleep is "
            print project_name
            status_id = config.CONSTS['status_success']
            update_command_status(inp_command_id, status_id)
            return JsonResponse({'success': True})



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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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


def designer_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    entry_time = datetime.now()
    try:
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/" )
    except OSError as e:  # excep path error
        error_num, error_msg = e
        if error_msg.strip() == "The system cannot find the file specified":
            # create directory
            os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/")
            # change directory
            os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/")

    # ------   create PDBS folder -----------
    os.system("mkdir " + config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + '/' + '/'+command_tool+"/"+md_mutation_folder+"/Analysis/Contact_score/pdbs/")

    # ---------  generate PDB frames from .XTC file   ----------------
    key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
    ProjectToolEssentials_protien_ligand_complex_index_number = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_protien_ligand_complex_index_number).latest(
            'entry_time')
    index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.values

    # ------   get TPR file   ------
    # get .tpr file from MD Simulations mutations folder(key = designer_mmpbsa_tpr_file)
    key_name_tpr_file = 'designer_mmpbsa_tpr_file'

    ProjectToolEssentials_res_tpr_file_input = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name_tpr_file).latest('entry_time')
    md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.values.replace('\\', '/')

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+config.PATH_CONFIG[
            'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n")

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_center.xtc -s " +
        config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o merged_fit.xtc -fit rot+trans -n")

    os.system(
        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_fit.xtc -s " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name  + "/"+command_tool+"/"+md_mutation_folder+"/"+ md_simulations_tpr_file + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+'Analysis/Contact_score' + "/frames_.pdb -split 1 -n")

    #copy python scripts (shared_scripts)
    shutil.copyfile(config.PATH_CONFIG[
            'local_shared_folder_path'] +"Contact_Score/readpdb2.py",config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + "/"+command_tool+"/"+md_mutation_folder+"/"+'Analysis/Contact_score/readpdb2.py')
    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + "Contact_Score/whole_protein_contact.py", config.PATH_CONFIG[
        'local_shared_folder_path'] + project_name + "/" + command_tool + "/" + md_mutation_folder + "/" + 'Analysis/Contact_score/whole_protein_contact.py')
    #get contact_score parameters from DB
    project_commands = commandDetails.objects.all().filter(project_id=project_id,
                                                                          command_title="CatMec",
                                                                          command_tool="Contact_Score",
                                                                          user_id=user_id).order_by("-command_id")
    print "0 th contact score command"
    print  project_commands[0].primary_command
    print "1 th contact score command"
    print  project_commands[1].primary_command
    # execute contact score command
    os.system(project_commands[0].primary_command)
    os.system(project_commands[1].primary_command)


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

        #Contact Score calculation for CatMec and Designer modules
        #Check for Command Title
        if commandDetails_result.command_title == "CatMec":
            #Execute for CatMec module
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)

            primary_command_runnable = commandDetails_result.primary_command

            # check command IF Contact calculation(C) or combine contact score(S)
            if primary_command_runnable.split()[3].strip() == "C":
                # change working directory
                try:
                    os.chdir(config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                except:  # excep path error
                    # error_num, error_msg = e
                    # if error_msg.strip() == "The system cannot find the file specified":
                    # create directory
                    os.system("mkdir " + config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)
                    # change directory
                    os.chdir(config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool)

                # copy Contact Score python scripts
                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + '/Contact_Score/whole_protein_contact.py',
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/" + "whole_protein_contact.py")

                shutil.copyfile(config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + '/Contact_Score/readpdb2.py',
                                config.PATH_CONFIG[
                                    'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/" + "readpdb2.py")

                # ------   create PDBS folder -----------
                os.system("mkdir " + config.PATH_CONFIG[
                    'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/pdbs")

                # ---------  generate PDB frames from .XTC file   ----------------
                key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
                ProjectToolEssentials_protien_ligand_complex_index_number = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_protien_ligand_complex_index_number).latest(
                        'entry_time')
                index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.values

                # ------   get TPR file   ------
                # get .tpr file from MD Simulations(key = mmpbsa_tpr_file)
                key_name_tpr_file = 'mmpbsa_tpr_file'

                ProjectToolEssentials_res_tpr_file_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_tpr_file).latest('entry_time')
                md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.values.replace('\\', '/')
                md_simulations_tpr_file_split = md_simulations_tpr_file.split("/")

                # create trajconv input file
                file_gmx_trajconv_input = open("gmx_trajconv_input.txt", "w")
                file_gmx_trajconv_input.write("1\n0\nq")
                file_gmx_trajconv_input.close()

                os.system(
                    "gmx trjconv -f " + config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                        'md_simulations_path'] + md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "complex_index.ndx < gmx_trajconv_input.txt")

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
                        'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                        'md_simulations_path'] + md_simulations_tpr_file + " -o " + config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_title + '/Analysis/' + commandDetails_result.command_tool + "/frames_.pdb -split 0 -sep -n " +
                    config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/CatMec/' + config.PATH_CONFIG[
                        'mmpbsa_project_path'] + "complex_index.ndx ")
            else: # primary_command_runnable.split()[3].strip() == "S":
                print "------   in contact score combine ----------"
                pass

            print "primary_command_runnable is -------------"
            print primary_command_runnable
            #execute contact score command
            print os.system(primary_command_runnable)
            return JsonResponse({"success": True})
            '''
            .-,--.                                          .     .      
            ' |   \ ,-. ,-. . ,-. ,-. ,-. ,-.   ,-,-. ,-. ,-| . . |  ,-. 
            , |   / |-' `-. | | | | | |-' |     | | | | | | | | | |  |-' 
            `-^--'  `-' `-' ' `-| ' ' `-' '     ' ' ' `-' `-' `-' `' `-' 
                               ,|                                        
                               `'                                        
            '''
        else: #Designer module
            #Execute for Designer module
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            with open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + 'Designer' + '/mutated_list.txt', 'r') as fp_mutated_list:
                mutated_list_lines = fp_mutated_list.readlines()
                variant_index_count = 0
                for line_mutant in mutated_list_lines:
                    # line_mutant ad mutation folder
                    # change working directory
                    try:
                        os.chdir(config.PATH_CONFIG[
                                     'local_shared_folder_path'] + project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")
                    except OSError as e:  # excep path error
                        error_num, error_msg = e
                        if error_msg.strip() == "The system cannot find the file specified":
                            # create directory
                            os.system("mkdir " + config.PATH_CONFIG[
                                'local_shared_folder_path'] + project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")
                            # change directory
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] + project_name + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/")

                    # ------   create PDBS folder -----------
                    os.system("mkdir " + config.PATH_CONFIG[
                        'local_shared_folder_path'] + project_name + '/' + '/' + 'Designer' + "/" + line_mutant + "/Analysis/Contact_score/pdbs/")

                    # ---------  generate PDB frames from .XTC file   ----------------
                    key_name_protien_ligand_complex_index_number = 'mmpbsa_index_file_protien_ligand_complex_number'
                    ProjectToolEssentials_protien_ligand_complex_index_number = \
                        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                   key_name=key_name_protien_ligand_complex_index_number).latest(
                            'entry_time')
                    index_file_complex_input_number = ProjectToolEssentials_protien_ligand_complex_index_number.values

                    # ------   get TPR file   ------
                    # get .tpr file from MD Simulations mutations folder(key = designer_mmpbsa_tpr_file)
                    key_name_tpr_file = 'designer_mmpbsa_tpr_file'

                    ProjectToolEssentials_res_tpr_file_input = \
                        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                   key_name=key_name_tpr_file).latest('entry_time')
                    md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.values.replace('\\', '/')

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f " + config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" +
                        config.PATH_CONFIG[
                            'mmpbsa_project_path'] + "merged.xtc -s " + config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o merged_center.xtc -center -pbc whole -ur compact -n")

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_center.xtc -s " +
                        config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o merged_fit.xtc -fit rot+trans -n")

                    os.system(
                        "echo " + index_file_complex_input_number + " | gmx trjconv -f merged_fit.xtc -s " + config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + md_simulations_tpr_file + " -o " +
                        config.PATH_CONFIG[
                            'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score' + "/frames_.pdb -split 1 -n")

                    # copy python scripts (shared_scripts)
                    shutil.copyfile(config.PATH_CONFIG[
                                        'local_shared_folder_path'] + "Contact_Score/readpdb2.py", config.PATH_CONFIG[
                                        'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score/readpdb2.py')
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + "Contact_Score/whole_protein_contact.py",
                                    config.PATH_CONFIG[
                                        'local_shared_folder_path'] + project_name + "/" + 'Designer' + "/" + line_mutant + "/" + 'Analysis/Contact_score/whole_protein_contact.py')

                    #execute Contact Score primary command
                    os.system(commandDetails_result.primary_command)

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
def md_simulation_preparation(inp_command_id,project_id,project_name,command_tool,command_title, md_simulation_path=''):
    status_id = config.CONSTS['status_initiated']
    update_command_status(inp_command_id, status_id)
    print "inside md_simulation_preparation function"
    key_name = 'md_simulation_no_of_runs'
    print('md_simulation_path is')
    print(md_simulation_path)
    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = int(ProjectToolEssentials_res.values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print md_run_no_of_conformation

    source_file_path = config.PATH_CONFIG['shared_folder_path'] + str(project_name) + md_simulation_path
    print('source file path in md simulation preparation --------------')
    print(source_file_path)
    print(source_file_path)
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
        os.chdir(source_file_path + '/md_run' + str(i + 1))
        print("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
        os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
        print("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
        os.system("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
        print("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")
        os.system("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")
        print("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")
        os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")
        group_value = sol_group_option()
        SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
        SOL_replace_str = SOL_replace_backup
        SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value[0]))
        print("printing group value in MD$$$$$$$$$$$$$$$$$$")
        print(group_value)
        print("printing after %SOL% replace")
        print(SOL_replace_str)
        os.system(SOL_replace_str)
        print("echo q | gmx make_ndx -f solve_ions.gro")
        os.system("echo q | gmx make_ndx -f solve_ions.gro")
        print("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
        os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
        print("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")
        os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")
        print("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
        os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
        print("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
        os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
        print("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
        os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
        print("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
        os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
        print("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
        os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
        print("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
        os.system("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")
    return JsonResponse({'success': True})\



def execute_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id, user_id):
    print "in execute_md_simulation definition"
    key_name = 'md_simulation_no_of_runs'

    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = int(ProjectToolEssentials_res.values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print md_run_no_of_conformation
    # copy MDP files to working directory
    MDP_filelist = ['em', 'ions', 'md', 'npt', 'nvt']
    for mdp_file in MDP_filelist:
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        + project_name + '/CatMec/MD_Simulation/' + mdp_file + '.mdp',
                        config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        + project_name + '/' + command_tool + '/' +str(md_mutation_folder)+"/"+ mdp_file + '.mdp')

    source_file_path = config.PATH_CONFIG['shared_folder_path'] + str(project_name) + "/"+command_tool + "/"+str(md_mutation_folder)+"/"
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
        print "in md_run loooppppp"
        print source_file_path + '/md_run' + str(i + 1)
        os.chdir(source_file_path + '/md_run' + str(i + 1))
        os.system("gmx editconf -f complex_out.gro -o  newbox.gro -bt cubic -d 1.2")
        os.system("gmx solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solve.gro")
        os.system("echo q | gmx make_ndx -f solve.gro > gromacs_solve_gro_indexing.txt")
        os.system("gmx grompp -f ions.mdp -po mdout.mdp -c solve.gro -p topol.top -o ions.tpr")

        group_value = sol_group_option()
        SOL_replace_backup = "echo %SOL_value% | gmx genion -s ions.tpr -o solve_ions.gro -p topol.top -neutral"
        SOL_replace_str = SOL_replace_backup
        SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value[0]))
        print("printing group value in MD$$$$$$$$$$$$$$$$$$")
        print(group_value)
        print("printing after %SOL% replace")
        print(SOL_replace_str)
        os.system(SOL_replace_str)
        os.system("echo q | gmx make_ndx -f solve_ions.gro")
        os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
        os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")

        # Hotspot MD RUN ends here ----
        os.system("gmx grompp -f nvt.mdp -po mdout.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -n index.ndx")
        os.system("gmx mdrun -v -s nvt.tpr -o nvt.trr -cpo nvt.cpt -c nvt.gro -e nvt.edr -g nvt.log -deffnm nvt")
        os.system("gmx grompp -f npt.mdp -po mdout.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr -n index.ndx")
        os.system("gmx mdrun -v -s npt.tpr -o npt.trr -cpo npt.cpt -c npt.gro -e npt.edr -g npt.log -deffnm npt")
        os.system("gmx grompp -f md.mdp -po mdout.mdp -c npt.gro -p topol.top -o md_0_1.tpr -n index.ndx")
        os.system("gmx mdrun -v -s md_0_1.tpr -o md_0_1.trr -cpo md_0_1.cpt -x md_0_1.xtc -c md_0_1.gro -e md_0_1.edr -g md_0_1.log -deffnm md_0_1")

    return JsonResponse({'success': True})


#Run MD Simulations for Hotspot module
def execute_hotspot_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id,
                                                  user_id,variant_dir_md):
    key_name = 'md_simulation_no_of_runs'

    ProjectToolEssentials_res = \
        ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                   key_name=key_name).latest('entry_time')

    md_run_no_of_conformation = 1 # int(ProjectToolEssentials_res.values)
    print ('md_run_no_of_conformation@@@@@@@@@@@@@@@@@@@@@@@@')
    print md_run_no_of_conformation
    # copy MDP files to working directory
    MDP_filelist = ['em', 'ions', 'md', 'npt', 'nvt']
    for mdp_file in MDP_filelist:
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        + project_name + '/CatMec/MD_Simulation/' + mdp_file + '.mdp',
                        config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                        + project_name + '/' + command_tool + '/' +str(md_mutation_folder)+"/"+variant_dir_md+"/"+ mdp_file + '.mdp')

    source_file_path = config.PATH_CONFIG['shared_folder_path'] + str(project_name) + "/"+command_tool + "/"+str(md_mutation_folder)+"/"+variant_dir_md+"/"
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
        SOL_replace_str = SOL_replace_str.replace('%SOL_value%', str(group_value[0]))
        print("printing group value in MD$$$$$$$$$$$$$$$$$$")
        print(group_value)
        print("printing after %SOL% replace")
        print(SOL_replace_str)
        os.system(SOL_replace_str)
        os.system("echo q | gmx make_ndx -f solve_ions.gro")
        os.system("gmx grompp -f em.mdp -po mdout.mdp -c solve_ions.gro -p topol.top -o em.tpr")
        os.system("gmx mdrun -v -s em.tpr -o em.trr -cpo em.cpt -c em.gro -e em.edr -g em.log -deffnm em")
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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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
            md_simulation_preparation(inp_command_id,project_id,project_name,commandDetails_result.command_tool,commandDetails_result.command_title)
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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)


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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< success try block homology modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< success except block homology modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print "error executing command!!"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< error try block homology modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< error except block homology modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)

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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name

        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

        print('before replacing primary_command_runnable')
        print(primary_command_runnable)

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
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< success try block loop modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< success except block loop modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})

        if process_return.returncode != 0:
            print "error executing command!!"
            fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log','w+')
            fileobj.write(err)
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< error try block loop modelling >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< error except block loop modelling  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
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
        print('before replacing primary_command_runnable')
        print(primary_command_runnable)
        #shared_scripts
        primary_command_runnable = re.sub("pdb_to_pdbqt.py", config.PATH_CONFIG['shared_scripts'] +str(command_tool)+ "/pdb_to_pdbqt.py",primary_command_runnable)
        primary_command_runnable = re.sub("%python_sh_path%",config.PATH_CONFIG['python_sh_path'],primary_command_runnable)
        primary_command_runnable = re.sub("%prepare_ligand4_py_path%",config.PATH_CONFIG['prepare_ligand4_py_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%add_python_file_path%",config.PATH_CONFIG['add_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%make_gpf_dpf_python_file_path%",config.PATH_CONFIG['make_gpf_dpf_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%grid_dock_map_python_file_path%",config.PATH_CONFIG['grid_dock_map_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%multiple_distance_python_file_path%",config.PATH_CONFIG['multiple_distance_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%multiple_angle_python_file_path%",config.PATH_CONFIG['multiple_angle_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%multiple_torsion_python_file_path%",config.PATH_CONFIG['multiple_torsion_python_file_path'],primary_command_runnable)
        # primary_command_runnable = re.sub("%input_folder_name%",config.PATH_CONFIG['local_shared_folder_path']+ project_name + '/' + commandDetails_result.command_tool + '/',primary_command_runnable)
        # primary_command_runnable = re.sub('%output_folder_name%', config.PATH_CONFIG[
        #     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/',
        #                                   primary_command_runnable)

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
        print "split is---------------------------------------------------------------------------------"
        print type(command_tool_title_split)
        print command_tool_title_split
        if(command_tool_title_split[0] == "nma"):
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+command_tool_title_split[2]+'/')

        elif(str(command_tool_title) == "tconcord_dlg"):
            enzyme_file_key = 'autodock_nma_final_protein_conformation'
            ProjectToolEssentials_autodock_enzyme_file_name = ProjectToolEssentials.objects.all().filter(
                project_id=project_id, key_name=enzyme_file_key).latest('entry_time')
            nma_enzyme_file = ProjectToolEssentials_autodock_enzyme_file_name.values
            nma_path = nma_enzyme_file[:-4]
            print(str(nma_path[:-4]))
            print('nma_path ****************************************')
            print(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+nma_path+'/')
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/tconcoord/'+nma_path+'/')
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
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)

            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
        if process_return.returncode != 0:
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(out)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)

            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)

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
    print('inside class CatMec')
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
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print "inside error"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error try block Ligand_Parametrization >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error except block Ligand_Parametrization  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        elif command_tool_title == "get_make_complex_parameter_details" or command_tool_title == "make_complex_params" or command_tool_title == "md_run":
            print 'command_tool_title ----------------------'
            print command_tool_title
            inp_command_id = request.POST.get("command_id")
            commandDetails_result = commandDetails.objects.get(command_id=inp_command_id)
            project_id = commandDetails_result.project_id
            QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
            project_name = QzwProjectDetails_res.project_name
            primary_command_runnable = commandDetails_result.primary_command
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            # QzwProjectEssentials_res = QzwProjectEssentials.objects.get(ppartial_charge_selection_nameroject_id=project_id)
            # ligand_name = QzwProjectEssentials_res.command_key
            # print "+++++++++++++++ligand name is++++++++++++"
            # print ligand_name
            os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + '/CatMec/MD_Simulation/')
            print (os.getcwd())

            if commandDetails_result.command_title == "md_run":
                md_simulation_path = '/CatMec/MD_Simulation/'
                print('md simulation path in md_run is')
                print(md_simulation_path)
                md_simulation_preparation(inp_command_id,project_id, project_name, commandDetails_result.command_tool,
                                          commandDetails_result.command_title,md_simulation_path)
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
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success try block get_make_complex_parameter_details or make_complex_params or md_run >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success except block get_make_complex_parameter_details or make_complex_params or md_run  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                print "inside error"
                fileobj = open(config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' + command_title_folder + '.log',
                               'w+')
                fileobj.write(err)
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error try block get_make_complex_parameter_details or make_complex_params or md_run >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error except block get_make_complex_parameter_details or make_complex_params or md_run  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
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
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success try block Catmec docking condition   >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< success except block Catmec docking condition   >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True,'output':out,'process_returncode':process_return.returncode})
            if process_return.returncode != 0:
                fileobj = open(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/'+commandDetails_result.command_tool+'/'+command_title_folder+'.log','w+')
                fileobj.write(err)
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error try block Catmec docking condition >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)
                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< error except block Catmec docking condition  >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)
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
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' )
        print os.system("pwd")
        primary_command_runnable = commandDetails_result.primary_command
        primary_command_runnable_split = primary_command_runnable.split(" ")
        if primary_command_runnable.strip() == "python run_md.py":
            #execute MD simulations
            primary_command_runnable = re.sub('python run_md.py', '', primary_command_runnable)
            md_simulation_preparation(inp_command_id,project_id, project_name, command_tool = commandDetails_result.command_tool,
                                      command_title = commandDetails_result.command_title)

        elif command_tool_title == "Designer_Mutations":
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
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
                    print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)

                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_success']
                    update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                try:
                    print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)

                except db.OperationalError as e:
                    print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    db.close_old_connections()
                    status_id = config.CONSTS['status_error']
                    update_command_status(inp_command_id, status_id)

                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})

        elif primary_command_runnable_split[1] == "make_complex.py":
            #Make Complex Execution
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/'+command_tool_title)

            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )

            print "execute command"
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                print "output of out is"
                print out
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})
        else:
            status_id = config.CONSTS['status_initiated']
            update_command_status(inp_command_id, status_id)
            process_return = Popen(
                args=primary_command_runnable,
                stdout=PIPE,
                stderr=PIPE,
                shell=True
            )

            print "execute command"
            out, err = process_return.communicate()
            process_return.wait()
            if process_return.returncode == 0:
                print "output of out is"
                print out
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
                return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
            if process_return.returncode != 0:
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)
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
        command_tool_title = commandDetails_result.command_title
        command_tool = commandDetails_result.command_tool
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        os.chdir(config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/' )
        print os.system("pwd")
        primary_command_runnable = commandDetails_result.primary_command

        # execute Hotspot Mutations
        # get python scripts
        shutil.copyfile(
            config.PATH_CONFIG['shared_scripts'] + commandDetails_result.command_tool + '/create_mutation.py',
            config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/create_mutation.py')
        shutil.copyfile(
            config.PATH_CONFIG['shared_scripts'] + commandDetails_result.command_tool + '/pymol_mutate.py',
            config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + commandDetails_result.command_tool + '/pymol_mutate.py')
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
                print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations success >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)

            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_success']
                update_command_status(inp_command_id, status_id)
            return JsonResponse({"success": True, 'output': out, 'process_returncode': process_return.returncode})
        if process_return.returncode != 0:
            try:
                print "<<<<<<<<<<<<<<<<<<<<<<< in try mutations error >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)

            except db.OperationalError as e:
                print "<<<<<<<<<<<<<<<<<<<<<<< in except mutations >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                db.close_old_connections()
                status_id = config.CONSTS['status_error']
                update_command_status(inp_command_id, status_id)

            return JsonResponse({"success": False, 'output': err, 'process_returncode': process_return.returncode})



#queue MAKE COMPLEX params command to DB
def queue_make_complex_params(request,project_id, user_id,  command_tool_title, command_tool, project_name):
    #get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "designer_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    designer_mutations_file = ProjectToolEssentials_mutations_file.values

    # open mutated text file and loop thru to prepare files for make_complex.py
    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              + project_name + '/' + command_tool + '/'+designer_mutations_file, 'r'
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
                      + project_name + '/' + command_tool +'/'+line.strip()+ '/variant_'+str(variant_index_count)+'.pdb', 'r'
                      ) as fp_variant_pdb:
                variant_pdb_lines = fp_variant_pdb.readlines()
                for line_pdb in variant_pdb_lines:
                    if line_pdb[0:6].strip() == "ATOM" or line_pdb[0:6].strip() == "HETAATM":
                        if line_pdb[22:26].strip() + "_" + line_pdb[17:20].strip() not in aminoacids_list:
                            # append all amino acids to list
                            aminoacids_list.append(line_pdb[22:26].strip() + "_" + line_pdb[17:20].strip())

            designer_protonation_matrix = ""
            protonation_ac_list = ["ASP", "GLU", "HIS", "LYS"]
            #copy protonation files from CatMex module to Designer
            for atoms_name in protonation_ac_list:
                try:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          + project_name + '/CatMec/MD_Simulation/'+atoms_name+"_protonate.txt",config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          + project_name + '/' + command_tool +'/'+line.strip()+"/"+atoms_name+"_protonate.txt")
                except IOError as e:
                    pass

            for atoms_name in protonation_ac_list:
                try:
                    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          + project_name + '/' + command_tool + '/' +line.strip()+"/"+ atoms_name + '_protonate.txt', 'r'
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
                          + project_name + '/' + command_tool +"/"+line.strip()+'/designer_final_matrix_pdb_pqr_protonate.txt')
                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          + project_name + '/' + command_tool +"/"+ line.strip()+'/protonate_input.txt')
            except:
                pass

            # prepare final matrix file of protonation values
            try:
                outFile = open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                               + project_name + '/' + command_tool +"/"+ line.strip() +'/designer_final_matrix_pdb_pqr_protonate.txt',
                               'w+')
                outFile.write(designer_protonation_matrix)
                outFile.close()
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)

            # prepare final protonation input text file
            with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                      + project_name + '/' + command_tool + "/" + line.strip() + '/protonate_input.txt', 'w+'
                      ) as input_file_ptr:
                with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                          + project_name + '/' + command_tool + "/" + line.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt', 'r'
                          ) as matrix_file_ptr:
                    matrix_file_lines = matrix_file_ptr.readlines()
                    for matrix_file_line in matrix_file_lines:
                        input_file_ptr.write(matrix_file_line.split()[5] + '\n')

            #get python script for make_compex execution
            shutil.copyfile(config.PATH_CONFIG['shared_scripts'] +'CatMec/MD_Simulation/' +"make_complex.py",
                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            + project_name + '/' + command_tool + "/" + line.strip() + "/" +"make_complex.py")

            #get make_complex parameters from DB
            make_complex_params_keyname = "make_complex_parameters"
            ProjectToolEssentials_make_complex_params = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=make_complex_params_keyname).latest('entry_time')
            make_complex_params = ProjectToolEssentials_make_complex_params.values

            variant_protien_file = 'variant_'+str(variant_index_count)+'.pdb'
            # replace protien file in make_complex_params
            make_complex_params_replaced = re.sub(r'(\w+)(\.pdb)', variant_protien_file, make_complex_params)

            #copy ligand .GRO files and .ITP files from CatMec module
            ligands_key_name = 'substrate_input'
            ProjectToolEssentials_ligand_name_res = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                               key_name=ligands_key_name).latest(
                'entry_time')
            ligand_names = ProjectToolEssentials_ligand_name_res.values
            ligand_file_data = ast.literal_eval(ligand_names)
            for key, value in ligand_file_data.items():
                #value.split('_')[0]
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                + project_name + '/CatMec/Ligand_Parametrization/' + str(value.split('_')[0]) + ".gro",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                + project_name + '/' + command_tool + '/' + line.strip() + "/" + str(value.split('_')[0]) + ".gro")
                # .ITP files
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                + project_name + '/CatMec/Ligand_Parametrization/' + str(value.split('_')[0]) + ".itp",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                + project_name + '/' + command_tool + '/' + line.strip() + "/" + str(
                                    value.split('_')[0]) + ".itp")

            #copy "ATOMTYPES" file from CatMec module
            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            + project_name + '/CatMec/Ligand_Parametrization/atomtypes.itp',
                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                            + project_name + '/' + command_tool + '/' + line.strip() + '/atomtypes.itp')

            #change DIR to Mutations list
            os.chdir(config.PATH_CONFIG[
                         'local_shared_folder_path'] + project_name + '/' + command_tool+ '/' +line.strip() +'/' )
            #execute make_complex.py
            print "execute make_complex.py-----------------"
            print make_complex_params_replaced
            print os.system("python3 make_complex.py "+make_complex_params_replaced)
            # queue command to database make_complex
            '''command_text_area = make_complex_params_replaced
            status = config.CONSTS['status_queued']
            comments = ""
            command_title_as_variant = line.strip()
            entry_time = datetime.now()
            result_insert_QZwProjectCommands = commandDetails(project_id=project_id, user_id=user_id,
                                                                  primary_command=command_text_area,
                                                                  entry_time=entry_time,
                                                                  status=status, command_tool=command_tool,
                                                                  command_title=command_title_as_variant, comments=comments)
            result = result_insert_QZwProjectCommands.save()'''
            '''
              ____                __  __ ____    ____  _                 _       _   _                 
             |  _ \ _   _ _ __   |  \/  |  _ \  / ___|(_)_ __ ___  _   _| | __ _| |_(_) ___  _ __  ___ 
             | |_) | | | | '_ \  | |\/| | | | | \___ \| | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \/ __|
             |  _ <| |_| | | | | | |  | | |_| |  ___) | | | | | | | |_| | | (_| | |_| | (_) | | | \__ \
             |_| \_\\__,_|_| |_| |_|  |_|____/  |____/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_|___/
            
            '''

            md_mutation_folder = line.strip()
            execute_md_simulation(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #EXECUTE MMPBSA
            '''
              ____                __  __ __  __ ____  ____ ____    _    
             |  _ \ _   _ _ __   |  \/  |  \/  |  _ \| __ ) ___|  / \   
             | |_) | | | | '_ \  | |\/| | |\/| | |_) |  _ \___ \ / _ \  
             |  _ <| |_| | | | | | |  | | |  | |  __/| |_) |__) / ___ \ 
             |_| \_\\__,_|_| |_| |_|  |_|_|  |_|_|   |____/____/_/   \_\
            
            '''
            #designer_queue_analyse_mmpbsa(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #EXECUTE CONTACT SCORE
            '''
               ____            _             _     ____                     
              / ___|___  _ __ | |_ __ _  ___| |_  / ___|  ___ ___  _ __ ___ 
             | |   / _ \| '_ \| __/ _` |/ __| __| \___ \ / __/ _ \| '__/ _ \
             | |__| (_) | | | | || (_| | (__| |_   ___) | (_| (_) | | |  __/
              \____\___/|_| |_|\__\__,_|\___|\__| |____/ \___\___/|_|  \___|
            '''
            #designer_queue_contact_score(request, md_mutation_folder, project_name, command_tool, project_id, user_id)

            #counter for next mutant folder
            variant_index_count +=1


#Hotspot module Make complex params
def hotspot_queue_make_complex_params(request, project_id, user_id, command_tool_title, command_tool, project_name):
    print "in  hotspot_queue_make_complex_params  definition =================="
    # get mutation filename from keyname (designer_input_mutations_file)
    key_mutations_filename = "hotspot_input_mutations_file"
    ProjectToolEssentials_mutations_file = ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                                      key_name=key_mutations_filename).latest(
        'entry_time')
    hotspot_mutations_file = ProjectToolEssentials_mutations_file.values
    print "hotspot mutation file --------"
    print "\n"
    print hotspot_mutations_file
    # open mutated text file and loop thru to prepare files for make_complex.py
    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              + project_name + '/' + command_tool + '/' + hotspot_mutations_file, 'r'
              ) as fp_mutated_list:
        mutated_list_lines = fp_mutated_list.readlines()
        variant_index_count = 0 # mutants entry
        for line in mutated_list_lines:
            print "in mutations folder !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! and folder name is"
            print line.strip()
            # ********** line loop in mutations file read ***********
            variant_index_dir = 0 # variant dirs counter
            for mutations_dirs in os.listdir(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
              + project_name + '/' + command_tool + '/' +line.strip()):
                # ---------- loop for variant dirs ---------------
                print "in mutants dir "
                print os.path.isdir(os.path.join(config.PATH_CONFIG[
                                                  'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + line.strip(),
                                              mutations_dirs))
                if os.path.isdir(os.path.join(config.PATH_CONFIG[
                                                  'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + line.strip(),
                                              mutations_dirs)):
                    # ------------ loop for mutations dir -----------------
                    print "print mutations_dirs"
                    print mutations_dirs
                    pdb_file_index_str = 0 # index for PDB (file) variant
                    for variants_dir in os.listdir(config.PATH_CONFIG[
                                                        'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs + "/"):
                        print "in variants dir ------"
                        print  "variant_"+str(pdb_file_index_str)+".pdb"
                        print variants_dir.endswith(".pdb")
                        print variants_dir.strip() == "variant_"+str(pdb_file_index_str)+".pdb"
                        # <<<<<<<<<<<<<< loop for variants dir >>>>>>>>>>>>>>>>>
                        if variants_dir.endswith(".pdb"):
                            # **************** PDB file  ********************"
                            print "with pdb dir ---------------------"
                            print config.PATH_CONFIG[
                                      'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + variants_dir.strip()

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
                                          'local_shared_folder_path_project'] + 'Project/' + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + variants_dir.strip(),
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
                                                    + project_name + '/CatMec/MD_Simulation/' + atoms_name + "_protonate.txt",
                                                    config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                    + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + atoms_name + "_protonate.txt")
                                except IOError as e:
                                    pass

                            for atoms_name in protonation_ac_list:
                                try:
                                    with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                              + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + atoms_name + "_protonate.txt",
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
                                          + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt')
                                os.remove(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                          + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/protonate_input.txt')
                            except:
                                pass

                            # prepare final matrix file of protonation values
                            try:
                                outFile = open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                               + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt',
                                               'w+')
                                outFile.write(designer_protonation_matrix)
                                outFile.close()
                            except IOError as (errno, strerror):
                                print "I/O error({0}): {1}".format(errno, strerror)

                            # prepare final protonation input text file
                            with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                      + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/protonate_input.txt',
                                      'w+'
                                      ) as input_file_ptr:
                                with open(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                          + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + '/designer_final_matrix_pdb_pqr_protonate.txt',
                                          'r'
                                          ) as matrix_file_ptr:
                                    matrix_file_lines = matrix_file_ptr.readlines()
                                    for matrix_file_line in matrix_file_lines:
                                        input_file_ptr.write(matrix_file_line.split()[5] + '\n')

                            # get python script for make_compex execution
                            shutil.copyfile(
                                config.PATH_CONFIG['shared_scripts'] + 'CatMec/MD_Simulation/' + "make_complex.py",
                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                + project_name + '/' + command_tool + "/" + line.strip() + "/" + mutations_dirs.strip() + "/" + "make_complex.py")

                            # get make_complex parameters from DB
                            make_complex_params_keyname = "make_complex_parameters"
                            ProjectToolEssentials_make_complex_params = \
                                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                                           key_name=make_complex_params_keyname).latest(
                                    'entry_time')
                            make_complex_params = ProjectToolEssentials_make_complex_params.values

                            variant_protien_file = 'variant_' + str(variant_index_count) + '.pdb'
                            # replace protien file in make_complex_params
                            make_complex_params_replaced = re.sub(r'(\w+)(\.pdb)', variants_dir.strip(),
                                                                  make_complex_params)

                            # copy ligand .GRO files and .ITP files from CatMec module
                            ligands_key_name = 'substrate_input'
                            ProjectToolEssentials_ligand_name_res = ProjectToolEssentials.objects.all().filter(
                                project_id=project_id,
                                key_name=ligands_key_name).latest(
                                'entry_time')
                            ligand_names = ProjectToolEssentials_ligand_name_res.values
                            ligand_file_data = ast.literal_eval(ligand_names)
                            for key, value in ligand_file_data.items():
                                # value.split('_')[0]
                                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                + project_name + '/CatMec/Ligand_Parametrization/' + str(
                                    value.split('_')[0]) + ".gro",
                                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + str(
                                                    value.split('_')[0]) + ".gro")
                                # .ITP files
                                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                + project_name + '/CatMec/Ligand_Parametrization/' + str(
                                    value.split('_')[0]) + ".itp",
                                                config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                                + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + str(
                                                    value.split('_')[0]) + ".itp")

                            # copy "ATOMTYPES" file from CatMec module
                            shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                            + project_name + '/CatMec/Ligand_Parametrization/atomtypes.itp',
                                            config.PATH_CONFIG['local_shared_folder_path_project'] + 'Project/'
                                            + project_name + '/' + command_tool + '/' + line.strip() + "/" + mutations_dirs.strip() + "/" + '/atomtypes.itp')

                            # change DIR to Mutations list
                            os.chdir(config.PATH_CONFIG[
                                         'local_shared_folder_path'] + project_name + '/' + command_tool + '/' + line.strip() + '/' + mutations_dirs.strip() + "/")
                            # execute make_complex.py
                            os.system(make_complex_params_replaced)

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
        QzwProjectDetails_res = QzwProjectDetails.objects.get(project_id=project_id)
        project_name = QzwProjectDetails_res.project_name
        primary_command_runnable = commandDetails_result.primary_command
        status_id = config.CONSTS['status_initiated']
        update_command_status(inp_command_id, status_id)

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
        md_simulations_tpr_file = ProjectToolEssentials_res_tpr_file_input.values.replace('\\', '/')

        # get .ndx file from MD Simulations(key = mmpbsa_tpr_file)
        key_name_ndx_file = 'designer_mmpbsa_index_file'

        ProjectToolEssentials_res_ndx_file_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                       key_name=key_name_ndx_file).latest('entry_time')
        md_simulations_ndx_file = ProjectToolEssentials_res_ndx_file_input.values.replace('\\', '/')

        key_name_CatMec_input = 'substrate_input'
        command_tootl_title = "CatMec"
        # get list of ligand inputs
        ProjectToolEssentials_res_CatMec_input = \
            ProjectToolEssentials.objects.all().filter(project_id=project_id, tool_title=command_tootl_title,
                                                       key_name=key_name_CatMec_input).latest('entry_time')
        CatMec_input_dict = ast.literal_eval(ProjectToolEssentials_res_CatMec_input.values)
        # if User has only one ligand as input
        multiple_ligand_input = False
        if len(CatMec_input_dict) > 1:
            multiple_ligand_input = True

        indexfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_indexfile_input.values)
        xtcfile_input_dict = ast.literal_eval(ProjectToolEssentials_res_xtcfile_input.values)

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
            md_xtc_files_str += config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/' + \
                                config.PATH_CONFIG['designer_md_simulations_path'] + xtcfile_inputvalue_formatted + " "
        gmx_trjcat_cmd = "gmx trjcat -f " + md_xtc_files_str + " -o " + config.PATH_CONFIG[
            'local_shared_folder_path'] + project_name + '/Designer/' + config.PATH_CONFIG[
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
            print "for multiple ligand input"
            #get user input ligand name from DB
            key_name_ligand_input = 'designer_mmpbsa_input_ligand'

            ProjectToolEssentials_res_ligand_input = \
                ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                           key_name=key_name_ligand_input).latest('entry_time')
            ligand_name = ProjectToolEssentials_res_ligand_input.values
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
            print reversed_indexfile_complex_option_input
            print reversed_indexfile_receptor_option_input
            maximum_key_ndx_input = max(indexfile_input_dict, key=indexfile_input_dict.get)
            receptor_index = indexfile_input_dict[maximum_key_ndx_input] + 1
            protien_ligand_complex_index = receptor_index + 1
            #write protien ligand complex index number to DB
            entry_time = datetime.now()
            key_name_protien_ligand_complex_index = 'designer_mmpbsa_index_file_protien_ligand_complex_number'
            ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials(tool_title=commandDetails_result.command_tool,
                                                                                      project_id=project_id,
                                                                                      key_name=key_name_protien_ligand_complex_index,
                                                                                      values=protien_ligand_complex_index,
                                                                                      entry_time=entry_time)
            result_ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer = ProjectToolEssentials_save_mmpbsa_protien_ligand_index_numer.save()
            ligand_name_index = protien_ligand_complex_index + 1
            file_gmx_make_ndx_input = open(config.PATH_CONFIG[
                                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                               'designer_md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(
                str(reversed_indexfile_receptor_option_input) + "\nname " + str(receptor_index) + " receptor\n" + str(reversed_indexfile_complex_option_input) + "\nname " + str(protien_ligand_complex_index) + " complex"+"\n"+str(ligand_name_input)+"\nname "+str(ligand_name_index)+" ligand"+ "\nq\n")
            file_gmx_make_ndx_input.close()

            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/Designer/' + config.PATH_CONFIG[
                               'designer_mmpbsa_path'] + "index.ndx < " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + "gmx_make_ndx_input.txt"

            print " make index command"
            print gmx_make_ndx
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
                                              'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                              'designer_md_simulations_path'] + "gmx_make_ndx_input.txt", "w")
            file_gmx_make_ndx_input.write(str(protein_index)+"\nname "+str(receptor_index)+" receptor\n"+str(protein_index)+" | "+str(ligandname_index)+"\nname "+str(protien_ligand_complex_index)+" complex")
            file_gmx_make_ndx_input.close()
            gmx_make_ndx = "gmx make_ndx -f " + config.PATH_CONFIG[
                'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_tpr_file + " -n " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                               'designer_md_simulations_path'] + md_simulations_ndx_file + " -o " + config.PATH_CONFIG[
                               'local_shared_folder_path'] + project_name + '/Designer/' + config.PATH_CONFIG[
                               'designer_mmpbsa_path'] + "complex_index.ndx <"+config.PATH_CONFIG[
                                              'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                              'designer_md_simulations_path'] + "gmx_make_ndx_input.txt"

            print " make index command"
            print gmx_make_ndx
            os.system(gmx_make_ndx)

        perform__designer_cmd_trajconv(project_name,project_id,md_simulations_tpr_file,md_simulations_ndx_file)
        #===================   post processing after make index  ===============================
        # copy MD .tpr file to MMPBSA working directory
        source_tpr_md_file = config.PATH_CONFIG[
                                 'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                 'designer_md_simulations_path'] + md_simulations_tpr_file
        tpr_file_split = md_simulations_tpr_file.split("/")
        dest_tpr_md_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                           config.PATH_CONFIG['designer_mmpbsa_path'] + tpr_file_split[1]

        shutil.copyfile(source_tpr_md_file, dest_tpr_md_file)

        # copy topology file from MS to MMPBSA working directory
        source_topology_file = config.PATH_CONFIG[
                                   'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                   'designer_md_simulations_path'] + tpr_file_split[0] + "/topol.top"
        dest_topology_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                             config.PATH_CONFIG['designer_mmpbsa_path'] + "topol.top"
        shutil.copyfile(source_topology_file, dest_topology_file)

        # copy ligand .itp files
        for ligand_inputkey, ligand_inputvalue in CatMec_input_dict.iteritems():
            ligand_name_split = ligand_inputvalue.split("_")
            source_itp_file = config.PATH_CONFIG[
                                  'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                                  'designer_md_simulations_path'] + tpr_file_split[0] + "/" + ligand_name_split[0] + ".itp"
            dest_itp_file = config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                            config.PATH_CONFIG['designer_mmpbsa_path'] + ligand_name_split[0] + ".itp"
            shutil.copyfile(source_itp_file, dest_itp_file)


        key_name_ligand_input = 'designer_mmpbsa_input_ligand'
        # processing itp files
        pre_process_designer_mmpbsa_imput(project_id, project_name, tpr_file_split, CatMec_input_dict, key_name_ligand_input)

        # ----------------------   make a "trail" directory for MMPBSA   -----------------------
        os.system("mkdir " + config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                  config.PATH_CONFIG['designer_mmpbsa_path'] + "trial")
        # copying MMPBSA input files to trail directory
        # copy .XTC file
        shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                        config.PATH_CONFIG['designer_mmpbsa_path'] + "merged-recentered.xtc",
                        config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                        config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/npt.xtc")

        # copy other input files for MMPBSA
        for file_name in os.listdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path']):
            # copy .TPR file
            if file_name.endswith(".tpr"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/npt.tpr")
            # copy .NDX file
            if file_name.endswith(".ndx"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/index.ndx")

            # copy .TOP file
            if file_name.endswith(".top"):
                shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/"+file_name)
            # copy .ITP files
            if file_name.endswith(".itp"):
                # renaming user input ligand as LIGAND
                key_name_ligand_input = 'designer_mmpbsa_input_ligand'

                ProjectToolEssentials_res_ligand_input = \
                    ProjectToolEssentials.objects.all().filter(project_id=project_id,
                                                               key_name=key_name_ligand_input).latest('entry_time')
                ligand_name = ProjectToolEssentials_res_ligand_input.values
                if file_name[:-4] == ligand_name:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/ligand.itp")
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/"+file_name)
                else:
                    shutil.copyfile(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + file_name,
                                    config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
                                    config.PATH_CONFIG['designer_mmpbsa_path'] + "trial/" + file_name)

        os.chdir(config.PATH_CONFIG['local_shared_folder_path'] + project_name + '/Designer/' + \
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

    try:
        os.system("mkdir " + config.PATH_CONFIG[
                     'local_shared_folder_path'] + project_name + '/' + config.PATH_CONFIG[
                     'designer_md_simulations_path'] + "Analysis/")
    except OSError as e:  # except path error
        if e.errno != os.errno.EEXIST:
            # directory already exists
            pass
        else:
            print e.errno
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
