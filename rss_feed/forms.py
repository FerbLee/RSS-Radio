# RSS-Radio - Online service for publishing radio broadcasting recordings and podcasts.
# Copyright (C) 2018  Fernando Liñares Varela
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on 15 Mar 2018

@author: fer
'''
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from .models import Station,Program,Broadcast,EXISTING_BCMETHODS,Comment,EXISTING_SHARING_OPTS,EXISTING_ADMIN_TYPES
from rss_feed.models import EXISTING_COMMENT_OPTIONS


class CountableWidget(forms.widgets.Textarea):
    
    class Media:
        js = ('javascript/Countable.js','javascript/countable-field.js')
    
    
    def render(self, name, value, attrs=None, **kwargs):
        
        final_attrs = self.build_attrs(self.attrs, attrs)

        if not isinstance(final_attrs.get('data-min-count'), int):
            final_attrs['data-min-count'] = 'false'
        if not isinstance(final_attrs.get('data-max-count'), int):
            final_attrs['data-max-count'] = 'false'

        output = super(CountableWidget, self).render(name, value, final_attrs, **kwargs)
        output += self.get_word_count_template(final_attrs)
        return mark_safe(output)
    
    
    @staticmethod
    def get_word_count_template(attrs):
        return (
                 '<span class="text-count" id="%(id)s_counter">Word count: '
                 '<span class="text-count-current">0</span></span>\r\n'
                 '<script type="text/javascript">var countableField = new CountableField("%(id)s")</script>\n'
               ) % {'id': attrs.get('id')}
               


class ImageFieldDisplay(forms.widgets.FileInput):
    
    #class Media():
    #    
    #    js = ('javascript/HandleFileSelect.js')


    def render(self, name, value, attrs=None, **kwargs):
        
        final_attrs = self.build_attrs(self.attrs, attrs)

        output = super(ImageFieldDisplay, self).render(name, value, final_attrs, **kwargs)
        output += self.get_image_preview_template(final_attrs)
        return mark_safe(output)
    
    
    @staticmethod
    def get_image_preview_template(attrs):

        return (
                 '<span class="img-prev" id="%(id)s_img-prev"></span>\r\n'
                 #'<output id="list"></output>'
                 '<output id="%(id)s-display"></output>'
                 '<script type="text/javascript">'
        
                    'function handleFileSelect2(evt) {'
                        'var files = evt.target.files;'
                        'var f = files[0];'
                        'var reader = new FileReader();'
    
                        'reader.onload = (function(theFile) {'
                            'return function(e) {'
                                'document.getElementById("%(id)s-display").innerHTML = [\'<p>New Image:</p>\',\'<img src="\', e.target.result,\'" title="\', theFile.name, \'" width="200"/>\'].join(\'\');'
                            '};'
                        '})(f);'

                        'reader.readAsDataURL(f);'
                        '}'
            
                 '    document.getElementById("%(id)s").addEventListener("change",handleFileSelect2, false);'                       
                 '</script>\n'
               ) % {'id': attrs.get('id')}


class SignUpForm(UserCreationForm):
    
    def __init__(self,*args, **kwargs):
    
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = _('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only')
        self.fields['password1'].help_text = _('<ul><li>Your password cannot be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password cannot be a commonly used password.</li><li>Your password cannot be entirely numeric.</li></ul>')
        self.fields['password2'].help_text = _('Enter the same password as before, for verification.')
        self.fields['email'].required = True    
        self.fields['email'].help_text = _('Required')
        
    location = forms.CharField(label=_('Location'),max_length=100,required=False)
    description = forms.CharField(label=_('Description'),widget=forms.Textarea,max_length=500,required=False)
    
    ifd = ImageFieldDisplay()
    avatar = forms.ImageField(label=_('Avatar'),widget=ifd,required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                 'location','description','avatar')


class EditUserForm(forms.ModelForm):
    
    location = forms.CharField(label='Location',max_length=100,required=False)
    #description = forms.CharField(label='Description',max_length=500,required=False)

    #cw = CountableWidget(attrs={'data-min-count': 5,'data-max-count': 90})
    description = forms.CharField(label=_('Description'),widget=forms.Textarea ,required=False)
    
    ifd = ImageFieldDisplay()
    avatar = forms.ImageField(label=_('Avatar'),widget=ifd,required=False)


    # Can't update username
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email','location','description','avatar')


class CustomChangePasswordForm(PasswordChangeForm):
    
    old_password = forms.CharField(label=_("Old password"),widget=forms.PasswordInput,required=False)
    new_password1 = forms.CharField(label=_("New password"),widget=forms.PasswordInput,required=False)
    new_password2 = forms.CharField(label=_("New password confirmation"),widget=forms.PasswordInput,required=False)
     

class IgnorePasswordEditForm(forms.ModelForm):
    
    ignore = forms.BooleanField(required=False,widget=HiddenInput)

    class Meta:
        model = User
        fields = ('ignore',) 


class AddProgramForm(forms.ModelForm):

    rss_link = forms.URLField(label=_('RSS Link'))
    #station = forms.ChoiceField(label=_('Station'),choices = (('cc',_('Community Channel')),),required=False)
    sharing_options = forms.ChoiceField(label=_('Sharing mode'),choices=EXISTING_SHARING_OPTS,required=False)
    comment_options = forms.ChoiceField(label=_('Enable episode comments'),choices=EXISTING_COMMENT_OPTIONS,required=False)
    website = forms.URLField(label=_('Website'),required=False)
    
    class Meta:
        model = Program
        fields = ('rss_link','website','sharing_options','comment_options')
    

class AddStationForm(forms.ModelForm):
    
    name = forms.CharField(label=_('Name'),max_length=200)

    #cw = CountableWidget(attrs={'data-min-count': 5,'data-max-count': 90})
    description = forms.CharField(label=_('Description'),max_length=500,widget=forms.Textarea,required=False)
    location = forms.CharField(label=_('Location'),max_length=200,required=False)
    profile_img = forms.ImageField(label=_('Profile Image'),widget=ImageFieldDisplay(),required=False)
    logo = forms.ImageField(label=_('Logo'),widget=ImageFieldDisplay(),required=False)
                
    broadcasting_method = forms.ChoiceField(label=_('Media'),widget=forms.Select(attrs = {'onchange' : "bcMethodFilter('id_form_station-broadcasting_method');"}),choices = EXISTING_BCMETHODS)
    
    broadcasting_area = forms.CharField(label=_('Area'),max_length=200,required=False)
    broadcasting_frequency = forms.CharField(label=_('Frequency'),max_length=200,required=False)
    streaming_link = forms.URLField(label=_('Streaming Link'),required=False)
    website = forms.URLField(label=_('Website'),required=False)
    
    class Meta:
        model = Station
        fields = ('name', 'logo', 'profile_img','broadcasting_method','broadcasting_area','broadcasting_frequency',
                  'streaming_link','description','website')


class CommentForm(forms.ModelForm):
    
    #cw = CountableWidget(attrs={'data-min-count': 5,'data-max-count': 90})
    text = forms.CharField(label=_('Text'),max_length=500,widget=forms.Textarea,required=True)
    
    
    def save(self, user, episode, commit=True, *args, **kwargs):
        
        comment = super(CommentForm, self).save(commit=False, *args, **kwargs)
        comment.user = user
        comment.episode = episode
        
        if commit:
            comment.save()
        
        return comment
        
        
    class Meta:
        model = Comment
        fields = ('text',)
    

class Select2Widget(forms.widgets.Select):
    
    def __init__(self,select_name,*args,**kwargs):
        super(Select2Widget, self).__init__(*args,**kwargs)
        self.select_name = select_name
    
    def render(self, name, value, attrs=None, **kwargs):
        
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['opts'] = self.choices
        final_attrs['select_name'] = self.select_name
        output = self.get_rich_select(final_attrs)
        return mark_safe(output)
    
    @staticmethod
    def get_rich_select(attrs):
        
        choice_list = attrs.get('opts')
       
        html_str = []
        
        for single_choice in choice_list:
            html_str.append('<option value="' + str(single_choice[0]) + '">' + str(single_choice[1]) + '</option>') 
        
        options_str = ''.join(html_str)
        
        return (
                 '<select name="' + attrs.get('select_name') + '" required="" id="%(id)s" class="js-example-basic-single" >'
                 + options_str + 
                 '</select>\n'
                 '<script type="text/javascript">'                    
                    '$(document).ready(function() {'
                    '$(\'.js-example-basic-single\').select2();'
                    '});\n'                     
                 '</script>\n'
               ) % {'id': attrs.get('id')}
    


class AddBroadcastForm(forms.ModelForm):
    

    def __init__(self,*args, **kwargs):
        
        try:
            pqs = kwargs.pop('program_qs')
        except KeyError:
            pqs = Program.objects.all()
            
        super(AddBroadcastForm, self).__init__(*args, **kwargs)
        self.fields['program'] = forms.ModelChoiceField(label=_('Program'),queryset=pqs ,widget=Select2Widget('program'))
        self.fields['schedule_details'] = forms.CharField(label=_('Broadcast Schedule'),max_length=100)
    
    
    class Meta:
        
        model = Broadcast
        fields = ('program','schedule_details')



class AddAdminForm(forms.Form):
    

    def __init__(self,*args, **kwargs):
        
        try:
            aqs = kwargs.pop('admin_qs')
        except KeyError:
            aqs = User.objects.all()
        
        try:
            cqs = kwargs.pop('choices_qs')
        except KeyError:
            cqs = EXISTING_ADMIN_TYPES
            
        super(AddAdminForm, self).__init__(*args, **kwargs)
        self.fields['admin'] = forms.ModelChoiceField(label=_('Administrator'),queryset=aqs ,widget=Select2Widget('admin'))
        self.fields['admin_type'] = forms.ChoiceField(label=_('Permissions'),choices = cqs)
    
    

class TextSearchForm(forms.Form):
    
    def __init__(self,*args, **kwargs):
    
        super(TextSearchForm, self).__init__(*args, **kwargs)
        self.fields['text'] = forms.CharField(label=_('Search'),max_length=200)
           
        
        