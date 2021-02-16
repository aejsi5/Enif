from rest_framework import serializers
from .models import *
from datetime import datetime


class Basic_Enif_Session_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Enif_Session
        fields = ['Token', 'Source', 'Valid_Until']

class Enif_Session_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Enif_Session
        fields = ['Token', 'Valid_Until', 'Source']
        read_only_fields = ('Token',)

class Basic_Intent_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Intent
        fields = ['ID', 'Name', 'Tag', 'Des']


class Basic_Enif_Request_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Enif_Request
        fields = ['ID', 'Pattern', 'Predict', 'Intent', 'Intent_Accuracy', 'User_Feedback', 'Inserted']

class Full_Enif_Request_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Enif_Request
        fields = '__all__'
        read_only_fields = ('ID', 'Inserted','LU', 'D')

