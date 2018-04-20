from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Episode, Program, Image, Station
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import SignUpForm, EditUserForm,CustomChangePasswordForm,IgnorePasswordEditForm,AddStationForm
from django.utils import timezone
from django.contrib.auth.models import User
import os
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext as _
from django.template import RequestContext
from rss_feed.forms import AddProgramForm

class IndexView(generic.ListView):
    
    template_name = 'rss_feed/index.html'
    #context_object_name = 'episode_list'

    def get_queryset_episodes(self):
        
        """Latest Episodes"""
        episodes = Episode.objects.order_by('-publication_date')[0:4]
        return episodes


    def get_queryset_programs(self):
        
        programs = Program.objects.order_by('-popularity')[4:]
        return programs
    
    def get_queryset(self):
        
        return self.get_queryset_episodes()
    
    def get_queryset_stations(self):
        
        stations = Station.objects.all()
        return stations
    
    def get_queryset_user_subscriptions(self):
        
        return Episode.objects.none()
    
    def get_queryset_user_stations(self):
        
        if self.request.user.is_authenticated():
            return self.request.user.followers.order_by('name')
        
        return Station.objects.none()
    
    def get_context_data(self, **kwargs):
        
        context = super(IndexView, self).get_context_data(**kwargs)
        context['episode_list'] = self.get_queryset_episodes()
        context['program_list'] = self.get_queryset_programs()
        context['station_list'] = self.get_queryset_stations()
        context['user_subs']    = self.get_queryset_user_subscriptions()
        context['user_stations'] = self.get_queryset_user_stations()
        
        return context
    

class ProgramDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Program
    template_name = 'rss_feed/detail_program.html'
        

class EpisodeDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Episode
    template_name = 'rss_feed/detail_episode.html'


class UserDetailView(generic.DetailView):
    
    model = User
    template_name = 'rss_feed/detail_user.html'    


class StationDetailView(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/detail_station.html'
    
    def get_queryset_episodes(self):
        
        return Episode.objects.none()
    
    def get_queryset_programs(self):
        
        return Program.objects.none()
    
    def get_queryset_followers(self):
    
        return self.object.followers.all()[0:7]
    
    def get_user_is_follower(self):
    
        return True if self.object.followers.filter(pk=self.request.user.id) else False
    
    def get_context_data(self, **kwargs):
        
        context = super(StationDetailView, self).get_context_data(**kwargs)
        context['episode_list'] = self.get_queryset_episodes()
        context['program_list'] = self.get_queryset_programs()
        context['follower_list'] = self.get_queryset_followers()
        context['is_follower'] = self.get_user_is_follower()
        
        return context


@login_required
def follow_station(request,**kwargs):
    
    new_follower = request.user
    
    station = Station.objects.filter(pk=kwargs['pk'])
    if station:
        station = station[0]
        station.followers.add(new_follower)

    return HttpResponseRedirect(reverse('rss_feed:detail_station' , args=(station.id,)))

@login_required
def unfollow_station(request,**kwargs):
    
    ex_follower = request.user
    
    station = Station.objects.filter(pk=kwargs['pk'])
    if station:
        station = station[0]
        station.followers.remove(ex_follower)

    return HttpResponseRedirect(reverse('rss_feed:detail_station', args=(station.id,)))


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


def create_logo(avatar_in_memory_instance,username):

#    try:
        
    if avatar_in_memory_instance != None:
    
        avatar_img = Image()
        avatar_img.path = avatar_in_memory_instance
        avatar_img.creation_date = timezone.now()
        avatar_img.name = os.path.basename(avatar_in_memory_instance._name)
        avatar_img.alt_text = username + '-logo'
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
     



@login_required
def add_content(request):
    
    if request.method == 'POST':
        
        form_station = AddStationForm(request.POST,prefix='form_station') 
        form_rss = AddProgramForm(request.POST,prefix='form_rss')
        
        if form_station.is_valid():
            
            station = Station()
            station.name = form_station.cleaned_data.get('name')
            
            form_station.logo = request.FILES.get('form_station-logo')
            station.logo = create_logo(form_station.logo,station.name)
            
            form_station.profile_img = request.FILES.get('form_station-profile_img')
            station.profile_img = create_logo(form_station.profile_img,station.name)
            
            station.broadcasting_method = form_station.cleaned_data.get('broadcasting_method')
            station.broadcasting_area = form_station.cleaned_data.get('broadcasting_area')
            station.broadcasting_frequency = form_station.cleaned_data.get('broadcasting_frequency')
            station.streaming_link = form_station.cleaned_data.get('streaming_link')
            station.description = form_station.cleaned_data.get('description')
            station.save()
            
            station.admins.add(request.user)
            station.followers.add(request.user)
            station.save()

            return HttpResponseRedirect(reverse('rss_feed:index', args=()))
        
        elif form_rss.is_valid():

            link = form_rss.cleaned_data.get("rss_link")
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


    else:
        
        form_station = AddStationForm(request.POST,prefix='form_station') 
        form_rss = AddProgramForm(request.POST,prefix='form_rss')
    
    return render(request, 'rss_feed/add_content.html', {'form_station': form_station,'form_rss': form_rss})
