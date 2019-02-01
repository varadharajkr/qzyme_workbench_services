from rest_framework import serializers
from .models import runCommands ,  serverDetails, commandDetails


class runCommandSerializer(serializers.ModelSerializer):

    class Meta:
        model = runCommands
        #fields = ('PreCommand', 'FileInput', 'Size' , 'NumRun')
        fields = '__all__'

class serverrDetailsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='idqzw_server_service_details')
    class Meta:
        model =serverDetails
        #fields = '__all__'
        fields = ('id','server_id','service_url','command_tool_id')

