'''
Created on 15 Mar 2018

@author: fer
'''
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext as _

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
    
    class Media():
        
        js = ('javascript/HandleFileSelect.js')


    def render(self, name, value, attrs=None, **kwargs):
        
        final_attrs = self.build_attrs(self.attrs, attrs)

        output = super(ImageFieldDisplay, self).render(name, value, final_attrs, **kwargs)
        output += self.get_image_preview_template(final_attrs)
        return mark_safe(output)
    
    
    @staticmethod
    def get_image_preview_template(attrs):
        return (
                 '<span class="img-prev" id="%(id)s_img-prev"></span>\r\n'
                 '<output id="list"></output>'
                 '<script type="text/javascript">'
                 'document.getElementById("%(id)s").addEventListener("change", handleFileSelect, false);'                       
                 '</script>\n'
               ) % {'id': attrs.get('id')}


class SignUpForm(UserCreationForm):
    
    location = forms.CharField(label=_('Location'),max_length=100,required=False)
    description = forms.CharField(label=_('Description'),max_length=500,required=False)
    
    ifd = ImageFieldDisplay()
    avatar = forms.ImageField(label=_('Avatar'),widget=ifd,required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                  'location','description','avatar')


class EditUserForm(forms.ModelForm):
    
    location = forms.CharField(label='Location',max_length=100,required=False)
    #description = forms.CharField(label='Description',max_length=500,required=False)

    cw = CountableWidget(attrs={'data-min-count': 5,'data-max-count': 90})
    description = forms.CharField(label=_('Description'),widget=cw,required=False)
    
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
    