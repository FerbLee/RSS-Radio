from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.views import generic
from .models import Episode, Program, Image, Station, Vote, Comment
from .models import EXISTING_VOTE_TYPES, LIKE_VOTE, DISLIKE_VOTE, NEUTRAL_VOTE,ADMT_OWNER
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import SignUpForm, EditUserForm,CustomChangePasswordForm,IgnorePasswordEditForm,AddStationForm,CommentForm
from django.utils import timezone
from django.contrib.auth.models import User
import os
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext as _
from django.template import RequestContext
from rss_feed.forms import AddProgramForm, AddBroadcastForm
from django.utils import timezone
from rss_feed.models import BCM_DIGITAL, BCM_FM, BCM_TV
from django.http.response import HttpResponseNotFound


class IndexView(generic.ListView):
    
    template_name = 'rss_feed/index.html'
    #context_object_name = 'episode_list'

    def get_queryset_episodes(self,nof_results):
        
        """Latest Episodes"""
        episodes = Episode.objects.order_by('-publication_date')[0:nof_results]
        return episodes


    def get_queryset_programs(self,nof_results):
        
        programs = Program.objects.order_by('-popularity')[0:nof_results]
        return programs
    
    def get_queryset(self):
        
        return Episode.objects.none()
    
    def get_queryset_stations(self):
        
        stations = Station.objects.all()
        return stations
    
    def get_queryset_user_subscriptions(self,nof_results):
        
        # Very inneficient. To be corrected
        if self.request.user.is_authenticated():
                    
            subs_programs = self.request.user.subscribers.all()
            subs_episodes = Episode.objects.none()
            
            for program in subs_programs:
                
                subs_episodes = program.episode_set.all()|subs_episodes
            
            return subs_episodes.order_by('-publication_date')[0:nof_results]
                
        return Episode.objects.none()
    
    
    def get_queryset_user_stations(self):
        
        if self.request.user.is_authenticated():
            return self.request.user.followers.order_by('name')
        
        return Station.objects.none()
    
    def get_context_data(self, **kwargs):
        
        nof_results=4
        
        context = super(IndexView, self).get_context_data(**kwargs)
        context['episode_list'] = self.get_queryset_episodes(nof_results)
        context['program_list'] = self.get_queryset_programs(nof_results)
        context['station_list'] = self.get_queryset_stations()
        context['user_subs']    = self.get_queryset_user_subscriptions(nof_results)
        context['user_stations'] = self.get_queryset_user_stations()
        
        return context


class ProgramDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Program
    template_name = 'rss_feed/detail_program.html'
    
    
    def get_user_is_subscriber(self):
    
        if self.request.user.is_authenticated():
            return self.request.user.subscribers.filter(pk=self.object.id)
        else:
            return Episode.objects.none()
        
        
    def get_episode_short_list(self,nof_results):
        
        return self.object.episode_set.order_by('-publication_date')[0:nof_results]


    def get_related_stations(self,nof_results):
        
        bc_qs = self.object.broadcast_set.all().prefetch_related('station')
        
        return [bc.station for bc in bc_qs][0:nof_results]
    

    def get_subscribers(self):
        
        return self.object.subscribers.all()
    
    
    def get_oldest_owner(self):
        
        owner = self.object.programadmin_set.filter(type=ADMT_OWNER[0]).order_by('date').prefetch_related('user')
        if owner:
            return owner[0].user
        
        return User.objects.none()
        

    def get_context_data(self, **kwargs):
        
        context = super(ProgramDetailView, self).get_context_data(**kwargs)
        context['is_subscriber'] = self.get_user_is_subscriber()
        context['episode_short_list'] = self.get_episode_short_list(nof_results=8)
        context['related_stations'] = self.get_related_stations(nof_results=4)
        context['subscribers'] = self.get_subscribers()
        context['owner'] = self.get_oldest_owner()
        context['is_admin'] = self.object.check_user_is_admin(self.request.user)
        
        return context


@login_required
def subscribe_program(request,**kwargs):
    
    new_subscriber = request.user
    program = Program.objects.filter(pk=kwargs['pk'])
    
    if program:
        program = program[0]
        program.subscribers.add(new_subscriber)

    return HttpResponseRedirect(reverse('rss_feed:detail_program' , args=(program.id,)))

@login_required
def unsubscribe_program(request,**kwargs):
    
    ex_subscriber = request.user
    program = Program.objects.filter(pk=kwargs['pk'])
    
    if program:
        program = program[0]
        program.subscribers.remove(ex_subscriber)

    return HttpResponseRedirect(reverse('rss_feed:detail_program' , args=(program.id,)))




class EpisodeDetailView(generic.edit.FormMixin,generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Episode
    form_class = CommentForm
    template_name = 'rss_feed/detail_episode.html'

    
    def get_success_url(self):
        
        return reverse('rss_feed:detail_episode', kwargs={'pk': self.object.id})

    
    def get_user_vote_type(self):
    
        if self.request.user.is_authenticated():
            vote = self.request.user.voters.filter(episode_id=self.object.id)
            if vote:
                vote = vote[0]
                return vote.type 
                    
        return NEUTRAL_VOTE[0]
    
    
    def get_comments_sorted(self):
    
        return self.object.comment_set.order_by('publication_date')
        
    
    def get_context_data(self, **kwargs):
        
        context = super(EpisodeDetailView, self).get_context_data(**kwargs)
        context['like_type'] = LIKE_VOTE[0]
        context['dislike_type'] = DISLIKE_VOTE[0]
        context['neutral_type'] = NEUTRAL_VOTE[0]
        context['upvotes'] = self.object.vote_set.filter(type=LIKE_VOTE[0]).count()
        context['downvotes'] = self.object.vote_set.filter(type=DISLIKE_VOTE[0]).count()
        context['user_vote_type'] = self.get_user_vote_type()
        context['comment_sorted_set'] = self.get_comments_sorted()
        context['comment_form'] = CommentForm(initial={'episode': self.object,'user':self.request.user})
        context['user_is_admin'] = self.object.check_user_is_admin(self.request.user)
        
        return context


    def post(self, request, *args, **kwargs):
        
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    
    def form_valid(self, form):
        
        form.save(user=self.request.user,episode=self.object)
        return super(EpisodeDetailView, self).form_valid(form)


@login_required
def delete_comment(request,**kwargs):
    
    if request.user.is_authenticated():    
   
        comment = Comment.objects.filter(pk=kwargs['cpk'])
    
        if comment: 
            
            comment = comment[0]
            if request.user.id == comment.user.id or comment.episode.check_user_is_admin(request.user):
                
                comment.removed = True
                comment.save()

            else:
                
                print("Non authorised comment deletion attempted by user " + str(request.user.id) + 
                      " " + request.user.username)
                return HttpResponseForbidden()
    
    return HttpResponseRedirect(reverse('rss_feed:detail_episode' , args=(kwargs['epk'],))) 
    

@login_required
def vote_episode(request,**kwargs):
        
    episode = Episode.objects.filter(pk=kwargs['pk'])
    new_vote_type = None
    
    for evt in EXISTING_VOTE_TYPES:
        if  kwargs['type'] == evt[0]:
            new_vote_type = kwargs['type']
            break;
    
    if new_vote_type == None:
        
        print("Unknown vote type " + str(kwargs['type']))
        return HttpResponseRedirect(reverse('rss_feed:detail_episode' , args=(kwargs['pk'],)))   
    
    if episode:
        
        episode = episode[0]
        vote =  episode.vote_set.filter(user_id=request.user.id)
        
        if vote:
            vote = vote[0]
            vote.refresh_from_db() 
            if vote.type != new_vote_type:                 
                vote.type = new_vote_type
                vote.date = timezone.now()
                vote.save()            
        else: 
            episode.vote_set.create(type=kwargs['type'],date=timezone.now(),user=request.user)

    return HttpResponseRedirect(reverse('rss_feed:detail_episode' , args=(kwargs['pk'],)))


class UserDetailView(generic.DetailView):
    
    model = User
    template_name = 'rss_feed/detail_user.html'    


    def get_followed_stations(self,nof_results):
        
        return self.object.followers.all()[0:nof_results]
    

    def get_subscriptions(self,nof_results):
        
        return self.object.subscribers.all()[0:nof_results]
    
    
    def get_owned_programs(self,nof_results):

        if self.request.user.is_authenticated():
            admin_qs = self.request.user.programs_admin.all().prefetch_related('program')[0:nof_results]
            return [admin.program for admin in admin_qs]
                
        else:
            return Program.objects.none()
    
    
    def get_owned_stations(self,nof_results):

        if self.request.user.is_authenticated():
            admin_qs = self.request.user.stations_admin.all().prefetch_related('station')[0:nof_results]
            return [admin.station for admin in admin_qs]
        else:
            return Program.objects.none()
    

    def get_context_data(self, **kwargs):
        
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context['follow_stations'] = self.get_followed_stations(nof_results=4)
        context['subscriptions'] = self.get_subscriptions(nof_results=4)
        context['owned_programs'] = self.get_owned_programs(nof_results=4)
        context['owned_stations'] = self.get_owned_stations(nof_results=4)
        
        return context


class StationDetailView(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/detail_station.html'
    
    def get_queryset_episodes(self,nof_results=4):    
                    
        subs_programs = self.object.programs.all()
        subs_episodes = Episode.objects.none()
        
        for program in subs_programs:
            
            subs_episodes = program.episode_set.all()|subs_episodes
        
        return subs_episodes.order_by('-publication_date')[0:nof_results]
                
    
    def get_queryset_programs(self,nof_results=8):
        
        return self.object.programs.all()[0:nof_results]
    
    def get_queryset_followers(self):
    
        return self.object.followers.all()[0:7]
    
    def get_user_is_follower(self):
        
        if self.request.user.is_authenticated():
            return self.request.user.followers.filter(pk=self.object.id)
        
        return User.objects.none()
    
    def apply_bc_specs(self):
        
        bc_apply_list = [BCM_DIGITAL[0],BCM_FM[0],BCM_TV[0]]
        
        return self.object.broadcasting_method in bc_apply_list
 
    
    def get_context_data(self, **kwargs):
        
        context = super(StationDetailView, self).get_context_data(**kwargs)
        context['episode_list'] = self.get_queryset_episodes()
        context['program_list'] = self.get_queryset_programs()
        context['follower_list'] = self.get_queryset_followers()
        context['is_follower'] = self.get_user_is_follower()
        context['is_admin'] = self.object.check_user_is_admin(self.request.user)
        #context['bcm_type'] = self.object.broadcasting_method
        context['apply_bc_specs'] = self.apply_bc_specs()
        
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
            
            station.location = form_station.cleaned_data.get('location')
            station.broadcasting_method = form_station.cleaned_data.get('broadcasting_method')
            station.broadcasting_area = form_station.cleaned_data.get('broadcasting_area')
            station.broadcasting_frequency = form_station.cleaned_data.get('broadcasting_frequency')
            station.streaming_link = form_station.cleaned_data.get('streaming_link')
            station.description = form_station.cleaned_data.get('description')
            station.website = form_station.cleaned_data.get('website')
            station.save()
            
            station.stationadmin_set.create(user=request.user,type=ADMT_OWNER[0])
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



@login_required
def station_edit(request,**kwargs):

    station = Station.objects.filter(pk=kwargs['pk'])
    
    if station:    
        station=station[0]
    else:
        print('Error in station_edit view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()

    if not station.check_user_is_admin(request.user):
        print('Error in station_edit view, user has no permissions to edit')
        return HttpResponseForbidden()
         
    if request.method == 'POST':
        
        form_station = AddStationForm(request.POST,instance=request.user,prefix='form_station') 
        
        if form_station.is_valid():
        
            station.name = form_station.cleaned_data.get('name')
            
            form_station.logo = request.FILES.get('form_station-logo')
            if form_station.logo != None:
                station.logo = create_logo(form_station.logo,station.name)
            
            form_station.profile_img = request.FILES.get('form_station-profile_img')
            if form_station.profile_img != None:
                station.profile_img = create_logo(form_station.profile_img,station.name)
            
            station.location = form_station.cleaned_data.get('location')
            station.broadcasting_method = form_station.cleaned_data.get('broadcasting_method')
            station.broadcasting_area = form_station.cleaned_data.get('broadcasting_area')
            station.broadcasting_frequency = form_station.cleaned_data.get('broadcasting_frequency')
            station.streaming_link = form_station.cleaned_data.get('streaming_link')
            station.description = form_station.cleaned_data.get('description')
            station.website = form_station.cleaned_data.get('website')
            station.save()
            
            return HttpResponseRedirect(reverse('rss_feed:detail_station', args=(station.id,)))
    
    else:
        form_station = AddStationForm(prefix='form_station',
                              initial={'name': station.name,
                                       'logo': station.logo,
                                       'profile_img': station.profile_img,
                                       'broadcasting_method': station.broadcasting_method,
                                       'broadcasting_area': station.broadcasting_area,
                                       'broadcasting_frequency': station.broadcasting_frequency,
                                       'streaming_link': station.streaming_link,
                                       'description': station.description,
                                       'location': station.location,
                                       'website': station.website})


    return render(request,'rss_feed/edit_station.html',{'station':station,'form_station': form_station})
    


@login_required
def program_edit(request,**kwargs):

    program = Program.objects.filter(pk=kwargs['pk'])
    
    if program:    
        program=program[0]
    else:
        print('Error in program_edit view, unknown program pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()
        
    if not program.check_user_is_admin(request.user):
        print('Error in program_edit view, user has no permissions to edit')
        return HttpResponseForbidden()

    if request.method == 'POST':
        
        form = AddProgramForm(request.POST) 
        
        if form.is_valid():
            
            program.rss_link = form.cleaned_data.get("rss_link")
            program.sharing_options = form.cleaned_data.get('sharing_options')
            program.save()
            
            return HttpResponseRedirect(reverse('rss_feed:detail_program', args=(program.id,)))
            
    else:
        form= AddProgramForm(initial={'rss_link': program.rss_link,
                                       'sharing_options': program.sharing_options})


    return render(request,'rss_feed/edit_program.html',{'program':program,'form': form})
   


class ManageStationView(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/manage_station.html'
    
    
    def get_queryset_broadcasts(self):
        
        return self.object.broadcast_set.all().prefetch_related('program')
        
    
    def get_queryset_admins(self):
    
        return self.object.stationadmin_set.all().prefetch_related('user')

        
    def get_context_data(self, **kwargs):
        
        context = super(ManageStationView, self).get_context_data(**kwargs)
        context['broadcast_list'] = self.get_queryset_broadcasts()
        context['admin_list'] = self.get_queryset_admins()
        context['is_admin'] = self.object.check_user_is_admin(self.request.user)
        context['add_broadcast_form'] = AddBroadcastForm()
         
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    
    

            
@login_required
def add_broadcast(request,**kwargs): 
    
    station = Station.objects.filter(pk=kwargs['pk'])
    
    if station:
        station = station[0]
    else: 
        print('Error in add_broadcast view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()
    
    if not station.check_user_is_admin(request.user):
        print('Error in program_edit view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden() 
    
    if request.method == 'POST':
        
        form = AddBroadcastForm(request.POST)
        
        if form.is_valid():
      
            program = form.cleaned_data.get('program')
            schedule = form.cleaned_data.get('schedule')
            station.broadcast_set.create(program=program,schedule_details=schedule)
    
    return HttpResponseRedirect(reverse('rss_feed:manage_station', args=(station.id,)))
    


@login_required
def delete_broadcast(request,**kwargs): 
    
    station = Station.objects.filter(pk=kwargs['spk'])
    
    if station:
        station = station[0]
    else: 
        print('Error in add_broadcast view, unknown station pk ' + str(kwargs['spk']))
        return HttpResponseNotFound()
    
    if not station.check_user_is_admin(request.user):
        print('Error in program_edit view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden()
    
    if request.method == 'POST':
      
        bc_qs = station.broadcast_set.filter(program_id=kwargs['ppk'])
        
        for broadcast in bc_qs:
            
            broadcast.delete()
    
    return HttpResponseRedirect(reverse('rss_feed:manage_station', args=(station.id,)))
    
    
    
    
    
