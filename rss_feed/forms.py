'''
Created on 15 Mar 2018

@author: fer
'''
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CountableWidget(forms.widgets.Textarea):
    
    class Media:
        js = (
            'javascript/Countable.js',
            'javascript/countable-field.js'
        )
    
    def render(self, name, value, attrs=None):
        
        #final_attrs = self.build_attrs(attrs)
        final_attrs = self.build_attrs(self.attrs, attrs)

        output = super(CountableWidget, self).render(name, value, final_attrs)
        output += """<span class="text-count" id="%(id)s_counter">Word count: <span class="text-count-current">0</span></span>""" \
          % {'id': final_attrs.get('id'),
             'min_count': final_attrs.get('text_count_min' or 'false'),
             'max_count': final_attrs.get('text_count_max' or 'false')}

        js = """
            <script type="text/javascript">
                var countableField = new CountableField("%(id)s")
            </script>
            """ % {'id': final_attrs.get('id')}


class ImageFieldDisplay(forms.widgets.FileInput):
    
    class Media():
        
        js = ('javascript/HandleFileSelect.js')

    
    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        # New Django
        #final_attrs = self.build_attrs(self.attrs, attrs)
        output = super(ImageFieldDisplay, self).render(name, value, final_attrs)
        output += """<span class="image-display" id="%(id)s_image_d">Word count: <span class="text-count-current">0</span></span>""" \
          % {'id': final_attrs.get('id'),
             'min_count': final_attrs.get('text_count_min' or 'false'),
             'max_count': final_attrs.get('text_count_max' or 'false')}


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
    #description = forms.CharField(label='Description',max_length=500,required=False)

    cw = CountableWidget(attrs={'data-min-count': 5,'data-max-count': 90})
    description = forms.CharField(label='Description',widget=cw,required=False)
    print(cw.media)
    print('AAAAAA')
    print(cw.__dict__)
    
    avatar = forms.ImageField(required=False)

    # Can't update username
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email','location','description','avatar')

        
