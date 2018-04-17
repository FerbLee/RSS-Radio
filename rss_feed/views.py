from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Episode, Program, Image
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import SignUpForm, EditUserForm,CustomChangePasswordForm,IgnorePasswordEditForm
from django.utils import timezone
from django.contrib.auth.models import User
import os
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext as _


class IndexView(generic.ListView):
    
    template_name = 'rss_feed/index.html'
    context_object_name = 'program_list'

    def get_queryset(self):
        
        """List of added programs"""
        return Program.objects.all()


class ProgramDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Program
    template_name = 'rss_feed/detail_program.html'

        

class EpisodeDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Episode
    template_name = 'rss_feed/detail_episode.html'


class UserDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = User
    template_name = 'rss_feed/detail_user.html'
    


def addLink(request):
    
    link = request.POST.get("rss_link")
    owner = request.user
    
    known_parsers = {'podomatic':rlp.ParserPodomatic(link,owner),'ivoox':rlp.ParserIvoox(link,owner),
                     'radioco':rlp.ParserRadioco(link,owner)}
    
    new_program_added = False
    for key,strategy in known_parsers.items():
    
        if key in link.lower():
            new_program_added = strategy.parse_and_save() 
    
    
    if not new_program_added:
        
        print('Could not identify parser per link. Trying with all of them')
        
        for key,strategy in known_parsers.items():
            
            if strategy.parse_and_save():
                new_program_added = True
                break;
    
    if not new_program_added:
        print('ERROR IN PARSING. PROGRAM NOT ADDED')
          
    return HttpResponseRedirect(reverse('rss_feed:index', args=()))



def AuthView(request):
    
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # Redirect to a success page.
        pass
    else:
        # Return an 'invalid login' error message.
        pass


def create_avatar(avatar_in_memory_instance,username):

#    try:
        
    if avatar_in_memory_instance != None:
    
        avatar_img = Image()
        avatar_img.path = avatar_in_memory_instance
        avatar_img.creation_date = timezone.now()
        avatar_img.name = os.path.basename(avatar_in_memory_instance._name)
        avatar_img.alt_text = username + '-avatar'
        avatar_img.save()
        
        return avatar_img
    
#    else:
#        raise Exception

#    except Exception as e:

    return Image.get_default_avatar()



def signup(request):
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.userprofile.description = form.cleaned_data.get('description')
            user.userprofile.location = form.cleaned_data.get('location')
            
            form.avatar = request.FILES.get('avatar')
            user.userprofile.avatar = create_avatar(form.avatar,user.username)
            
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
        
            return HttpResponseRedirect(reverse('rss_feed:index', args=()))
    
    else:
        form = SignUpForm()
       
    return render(request, 'registration/signup.html', {'form': form})


def user_atb_form_handler(req,user_atb_form,avatar_key='avatar'):

    req.user.userprofile.description = user_atb_form.cleaned_data.get('description')
    req.user.userprofile.location = user_atb_form.cleaned_data.get('location')
        
    user_atb_form.avatar = req.FILES.get(avatar_key)

    if user_atb_form.avatar != None:
        req.user.userprofile.avatar = create_avatar(user_atb_form.avatar,req.user.username)
    
    req.user.save()


@login_required
def user_edit(request):
   
    # This body will only run if the user is logged in
    # and the current logged in user will be in request.user

    if request.method == 'POST':
        
        form = EditUserForm(request.POST,instance=request.user,prefix='form_atb') 
        formp = CustomChangePasswordForm(user=request.user,data=request.POST,prefix='form_pass')
        formi = IgnorePasswordEditForm(request.POST,prefix='form_ignore_p')
        
        if formi.is_valid():
            
            if formi.cleaned_data.get('ignore'):
                
                if form.is_valid():
               
                    user_atb_form_handler(request,form,'form_atb-avatar')
   
                    return HttpResponseRedirect(reverse('rss_feed:detail_user', args=(request.user.id,)))
                
            else:
                if form.is_valid() and formp.is_valid():
                    
                    user_atb_form_handler(request,form,'form_atb-avatar')
                    
                    user = formp.save()
                    update_session_auth_hash(request, user)  # Important!
                    messages.success(request, 'Your password was successfully updated!')
            
                    return HttpResponseRedirect(reverse('rss_feed:detail_user', args=(request.user.id,)))
                
                else:
                    
                    return render(request,'rss_feed/edit_user.html',{'form_atb': form,'form_pass':formp,
                                                                     'form_ignore_p':formi,'password_show':1})
    
    else:
        form = EditUserForm(prefix='form_atb',
                            initial={'location':request.user.userprofile.location,
                                     'description':request.user.userprofile.description,
                                     'first_name':request.user.first_name,
                                     'last_name':request.user.last_name,
                                     'email':request.user.email})
        formp = CustomChangePasswordForm(user=request.user,prefix='form_pass')
        formi = IgnorePasswordEditForm(prefix='form_ignore_p',initial={'ignore':True})

    return render(request,'rss_feed/edit_user.html',{'form_atb': form,'form_pass':formp,'form_ignore_p':formi,
                                                     'password_show':0})
     
