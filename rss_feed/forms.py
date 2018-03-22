'''
Created on 15 Mar 2018

@author: fer
'''
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    
    location = forms.CharField(label='Location',max_length=100,required=False)
    description = forms.CharField(label='Description',max_length=500,required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                  'location','description','avatar')


class EditUserForm(forms.ModelForm):
    
    location = forms.CharField(label='Location',max_length=100,required=False)
    description = forms.CharField(label='Description',max_length=500,required=False)
    avatar = forms.ImageField(required=False)

    # Can't update username
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email','location','description','avatar')
    
        
