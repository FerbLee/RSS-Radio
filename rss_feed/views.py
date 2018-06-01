from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.views import generic
from .models import Episode, Program, Image, Station, Vote, Comment, Broadcast, Tag
from .models import EXISTING_VOTE_TYPES, LIKE_VOTE, DISLIKE_VOTE, NEUTRAL_VOTE,ADMT_OWNER,EXISTING_ADMIN_TYPES
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import SignUpForm, EditUserForm,CustomChangePasswordForm,IgnorePasswordEditForm,AddStationForm, \
    CommentForm,AddAdminForm,TextSearchForm
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
from rss_feed.models import BCM_DIGITAL, BCM_FM, BCM_TV, SHAREABLE_OPTIONS,\
    ADMT_ADMIN, StationAdmin, ProgramAdmin, CO_ENABLE, SH_TF, SH_AF
from django.http.response import HttpResponseNotFound
from .search_view_functions import textbox_search_episode, textbox_search_program, textbox_search_station, \
    textbox_search_user,get_tag_cloud
from django.http import HttpResponse

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
        context['comments_allowed'] = self.object.check_comments_enabled()
        
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
 
    def get_user_is_admin(self):
        
        if self.request.user.is_authenticated():
            return self.object.check_user_is_admin(self.request.user)
        else:
            return User.objects.none()
    
    def get_context_data(self, **kwargs):
        
        context = super(StationDetailView, self).get_context_data(**kwargs)
        context['episode_list'] = self.get_queryset_episodes()
        context['program_list'] = self.get_queryset_programs()
        context['follower_list'] = self.get_queryset_followers()
        context['is_follower'] = self.get_user_is_follower()
        context['is_admin'] = self.get_user_is_admin()
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

            return HttpResponseRedirect(reverse('rss_feed:detail_station', args=(station.id,)))
        
        elif form_rss.is_valid():

            link = form_rss.cleaned_data.get("rss_link")
            owner = request.user
        
            known_parsers = {'podomatic':rlp.ParserPodomatic(link,owner),'ivoox':rlp.ParserIvoox(link,owner),
                             'radioco':rlp.ParserRadioco(link,owner)}
        
            new_program_added = None
        
            for key,strategy in known_parsers.items():
        
                if key in link.lower():
                    new_program_added = strategy.parse_and_save() 
        
            if new_program_added == None:  
                  
                print('Could not identify parser per link. Trying with all of them')
                
                for key,strategy in known_parsers.items():
                    
                    new_program_added = strategy.parse_and_save()
                    if new_program_added != None:
                        break;
                    
            if new_program_added == None:
                print('ERROR IN PARSING. PROGRAM NOT ADDED')
                return HttpResponseNotFound()
            
            # Save RSS non related atbs
            new_program_added.website = form_rss.cleaned_data.get('website')
            new_program_added.comment_options = form_rss.cleaned_data.get('comment_options')
            new_program_added.sharing_options = form_rss.cleaned_data.get('sharing_options')
            
            new_program_added.save()
            
            return HttpResponseRedirect(reverse('rss_feed:detail_program', args=(new_program_added.id,)))

    else:
        
        form_station = AddStationForm(request.POST,prefix='form_station') 
        form_rss = AddProgramForm(request.POST,prefix='form_rss',initial={'sharing-options':SH_TF[0],'comment-options':CO_ENABLE[0]})
    
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
            program.website = form.cleaned_data.get('website')
            program.comment_options = form.cleaned_data.get('comment_options')
            program.save() 
            
            return HttpResponseRedirect(reverse('rss_feed:detail_program', args=(program.id,)))
            
    else:
        form= AddProgramForm(initial={'rss_link': program.rss_link,
                                       'sharing_options': program.sharing_options,
                                       'website':program.website,
                                       'comment_options':program.comment_options})


    return render(request,'rss_feed/edit_program.html',{'program':program,'form': form})
   


class ManageStationView(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/manage_station.html'
    
    
    def get_queryset_broadcasts(self):
        
        return self.object.broadcast_set.order_by('program__name').prefetch_related('program')
        
    
    def get_queryset_admins(self):
    
        return self.object.stationadmin_set.all().prefetch_related('user')

    
    def get_elegible_programs(self):
        
        sh_group = [x[0] for x in SHAREABLE_OPTIONS]
        
        shareable_programs = Program.objects.filter(sharing_options__in=sh_group)
        already_in_station = self.object.programs.all()
        
        return shareable_programs.difference(already_in_station)
    
        
    def get_context_data(self, **kwargs):
        
        context = super(ManageStationView, self).get_context_data(**kwargs)
        context['broadcast_list'] = self.get_queryset_broadcasts()
        context['admin_list'] = self.get_queryset_admins()
        context['is_admin'] = self.object.check_user_is_admin(self.request.user)
        
        kwargs = {"program_qs":self.get_elegible_programs()}
        
        bc_form = AddBroadcastForm(**kwargs)
        context['add_broadcast_form'] = bc_form
        
         
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
            schedule = form.cleaned_data.get('schedule_details')
            
            if program.sharing_options == SH_AF[0]:
                messages.success(request, _('Program') + ' ' + program.name + ' ' + _(' needs approval to be broadcasted. A request was sent.'),extra_tags='add')
            elif program.sharing_options == SH_TF[0]:    
                station.broadcast_set.create(program=program,schedule_details=schedule)
                messages.success(request, _('Program') + ' ' + program.name + ' ' + _('was successfully added!'),extra_tags='add')
             
        else:
            print('ERROR')
            print(form.errors)
    
        
    return HttpResponseRedirect(reverse('rss_feed:manage_station', args=(station.id,)))
    
    
@login_required
def delete_broadcast(request,**kwargs): 
    
    station = Station.objects.filter(pk=kwargs['pk'])
    
    if station:
        station = station[0]
    else: 
        print('Error in delete_broadcast view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()
    
    if not station.check_user_is_admin(request.user):
        print('Error in delete_broadcast view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden()
    
    selected_prefix = 'check-'
    schedule_field_prefix = 'schedule-'
    check_counter = 0

    if 'bcremove' in request.POST.keys():
        print("REMOVE")
        for key in request.POST.keys():
            if selected_prefix in key:
                check_counter+=1
                Broadcast.objects.filter(pk=request.POST.get(key)).delete()
        
        if check_counter==1:  
            messages.success(request,str(check_counter) + ' ' + _('program was successfully removed.'),extra_tags='edit')      
        elif check_counter > 1:
            messages.success(request,str(check_counter) + ' ' + _('programs were successfully removed.'),extra_tags='edit')
    
    else: 
        print("UPDATE")
        for key in request.POST.keys():
            if selected_prefix in key:
                bc_id = request.POST.get(key)
                bcqs = Broadcast.objects.filter(pk=bc_id)
                check_counter+=1
                if bcqs:
                    bc=bcqs[0]
                    bc.schedule_details = request.POST.get(schedule_field_prefix + str(bc_id)) 
                    bc.save()
        
        if check_counter==1:  
            messages.success(request,str(check_counter) + ' ' + _('program was successfully updated.'),extra_tags='edit')      
        elif check_counter > 1:
            messages.success(request,str(check_counter) + ' ' + _('programs were successfully updated.'),extra_tags='edit')
    
    if check_counter == 0:
        messages.error(request, _('No program was selected. Please, check the program lines in order to commit the changes.'),extra_tags='edit')                
    
    return HttpResponseRedirect(reverse('rss_feed:manage_station', args=(station.id,)))
    
    

class AdminStationView(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/admin_station.html'
    
        
    def get_queryset_admins(self):
    
        return self.object.stationadmin_set.order_by('user__username').prefetch_related('user')

    
    def get_elegible_users(self):
        
        already_admins = self.object.admins.all()
        
        return User.objects.all().difference(already_admins).order_by('username')
    
        
    def get_context_data(self, **kwargs):
        
        context = super(AdminStationView, self).get_context_data(**kwargs)
        context['admin_list'] = self.get_queryset_admins()
        context['is_owner'] = self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0])
        context['station_class_id'] = Station.class_str_id()
        
        kwargs = {'admin_qs':self.get_elegible_users()}
        #Check if not owner
        if not self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0]):
            kwargs['choices_qs'] = (ADMT_ADMIN,)    
        admin_form = AddAdminForm(**kwargs,initial={'admin_type': ADMT_ADMIN[0]})
        context['add_admin_form'] = admin_form
        
        context['permissions_available'] = dict(EXISTING_ADMIN_TYPES)
        context['owner_permissions'] = ADMT_OWNER
        
         
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    
    
    
    
class AdminProgramView(generic.DetailView):
    
    model = Program
    template_name = 'rss_feed/admin_program.html'
    
        
    def get_queryset_admins(self):
    
        return self.object.programadmin_set.order_by('user__username').prefetch_related('user')

    
    def get_elegible_users(self):
        
        already_admins = self.object.admins.all()
        
        return User.objects.all().difference(already_admins).order_by('username')
    
        
    def get_context_data(self, **kwargs):
        
        context = super(AdminProgramView, self).get_context_data(**kwargs)
        context['admin_list'] = self.get_queryset_admins()
        context['is_owner'] = self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0])
        context['program_class_id'] = Program.class_str_id()
        
        kwargs = {'admin_qs':self.get_elegible_users()}
        #Check if not owner
        if not self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0]):
            kwargs['choices_qs'] = (ADMT_ADMIN,)    
        admin_form = AddAdminForm(**kwargs,initial={'admin_type': ADMT_ADMIN[0]})
        context['add_admin_form'] = admin_form
        
        context['permissions_available'] = dict(EXISTING_ADMIN_TYPES)
        context['owner_permissions'] = ADMT_OWNER
        
         
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    
    
    

def admin_validator(user,view_display_name,**kwargs):

    entity_pk = kwargs['pk']
    
    if  kwargs['type'] == Station.class_str_id():
        
        next_view = 'rss_feed:admin_station'
        entity = Station.objects.filter(pk=entity_pk)
    
    elif kwargs['type'] == Program.class_str_id():
       
        next_view = 'rss_feed:admin_program'
        entity = Program.objects.filter(pk=entity_pk) 

    else:
        
        print('Error in' + view_display_name + ' view, invalid station or program pk ' + str(entity_pk))
        return HttpResponseNotFound()
        
    if entity:
        entity = entity[0]
    else: 
        print('Error in ' + view_display_name + ' view, unknown station or program pk ' + str(entity_pk))
        return HttpResponseNotFound()
    
    if not entity.check_user_is_admin(user):
        print('Error in ' + view_display_name + ' view, user ' + str(user.id) + '-' + str(user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden() 

    return (entity,next_view)


@login_required
def add_admin(request,**kwargs): 
    
    view_display_name = 'add_admin'
    entity,next_view = admin_validator(request.user,view_display_name,**kwargs)
    
    if request.method == 'POST':
        
        form = AddAdminForm(request.POST)
        
        if form.is_valid():
      
            new_admin = form.cleaned_data.get('admin')
            
            #Check if owner
            if entity.check_user_is_admin(request.user,ADMT_OWNER[0]):
                new_admin_type = form.cleaned_data.get('admin_type')
            else:
                new_admin_type = ADMT_ADMIN[0]
                
            if kwargs['type'] == Station.class_str_id():
                entity.stationadmin_set.create(user=new_admin,type=new_admin_type)
            else:
                entity.programadmin_set.create(user=new_admin,type=new_admin_type)
            
            permission_dict = dict(EXISTING_ADMIN_TYPES)
            messages.success(request, _('User') + ' ' + new_admin.username + ' ' + _('was successfully added as')+ ' ' + permission_dict[new_admin_type],
                             extra_tags='add')
        
        else:
            print('ERROR')
            print(form.errors)
    
 
    return HttpResponseRedirect(reverse(next_view, args=(entity.id,)))


@login_required
def edit_admin(request,**kwargs): 
    
    view_display_name = 'edit_admin'
    entity,next_view = admin_validator(request.user,view_display_name,**kwargs)
    
    selected_prefix = 'check-'
    permission_field_prefix = 'permission-'
    check_counter = 0

    if 'adremove' in request.POST.keys():
        print("REMOVE")
        if kwargs['type'] == Station.class_str_id():
            for key in request.POST.keys():
                if selected_prefix in key:
                    check_counter += 1
                    StationAdmin.objects.filter(pk=request.POST.get(key)).delete()
        else:
            for key in request.POST.keys():
                if selected_prefix in key:
                    check_counter += 1
                    ProgramAdmin.objects.filter(pk=request.POST.get(key)).delete()
        
        if check_counter==1:  
            messages.success(request,str(check_counter) + ' ' + _('admin was successfully removed.'),extra_tags='edit')      
        elif check_counter > 1:
            messages.success(request,str(check_counter) + ' ' + _('admin were successfully removed.'),extra_tags='edit')
                
    else: 
        print("UPDATE")
        if kwargs['type'] == Station.class_str_id():
            for key in request.POST.keys():
                if selected_prefix in key:
                    check_counter += 1
                    adm_id = request.POST.get(key)
                    admqs = StationAdmin.objects.filter(pk=adm_id)
                    if admqs:
                        adm=admqs[0]
                        adm.type = request.POST.get(permission_field_prefix+ str(adm_id)) 
                        adm.save()
        else:
            for key in request.POST.keys():
                if selected_prefix in key:
                    check_counter += 1
                    adm_id = request.POST.get(key)
                    admqs = ProgramAdmin.objects.filter(pk=adm_id)
                    if admqs:
                        adm=admqs[0]
                        adm.type = request.POST.get(permission_field_prefix+ str(adm_id)) 
                        adm.save()
        
        if check_counter==1:  
            messages.success(request,str(check_counter) + ' ' + _('admin was successfully updated.'),extra_tags='edit')      
        elif check_counter > 1:
            messages.success(request,str(check_counter) + ' ' + _('admin were successfully updated.'),extra_tags='edit')
    
    if check_counter == 0:
        messages.error(request, _('No admin was selected. Please, check the admin lines in order to commit the changes.'),extra_tags='edit')                
   
    return HttpResponseRedirect(reverse(next_view, args=(entity.pk,)))



class DeleteStationPreview(generic.DetailView):
    
    model = Station
    template_name = 'rss_feed/predelete_station.html'
    
        
    def get_queryset_admins(self):
    
        return self.object.stationadmin_set.order_by('user__username').prefetch_related('user')
    
        
    def get_context_data(self, **kwargs):
        
        context = super(DeleteStationPreview, self).get_context_data(**kwargs)
        context['admin_list'] = self.get_queryset_admins()
        context['is_owner'] = self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0])
        context['permissions_available'] = dict(EXISTING_ADMIN_TYPES)
        context['owner_permissions'] = ADMT_OWNER
        
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    


@login_required
def delete_station(request,**kwargs):
    
    station = Station.objects.filter(pk=kwargs['pk'])
    view_display_name = 'delete_station'
    
    if station:
        station = station[0]
    else: 
        print('Error in ' + view_display_name + ' view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()    
    
    if not station.check_user_is_admin(request.user,ADMT_OWNER[0]):
        print('Error in ' + view_display_name + ' view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden() 
    
    if request.method == 'POST':
    
        station.delete()
        return HttpResponseRedirect(reverse('rss_feed:deleted', args=()))
    
   
@login_required    
def deleted_content(request,**kwargs):
    
    return render(request, 'rss_feed/deleted.html')
    
    
    

class ManageProgramView(generic.DetailView):
    
    model = Program
    template_name = 'rss_feed/manage_program.html'
    
    
    def get_queryset_broadcasts(self):
        
        return self.object.broadcast_set.order_by('station__name').prefetch_related('station')
        
    
    def get_queryset_admins(self):
    
        return self.object.stationadmin_set.all().prefetch_related('user')

    
    def get_station_set(self):
        
        all_stations = Station.objects.all()
        broadcasting_stations = self.object.station_set.all()
        
        return all_stations.difference(broadcasting_stations)
    
        
    def get_context_data(self, **kwargs):
        
        context = super(ManageProgramView, self).get_context_data(**kwargs)
        context['broadcast_list'] = self.get_queryset_broadcasts()
        #context['admin_list'] = self.get_queryset_admins()
        context['is_admin'] = self.object.check_user_is_admin(self.request.user)
        
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    
    

@login_required
def program_delete_broadcast(request,**kwargs): 
    
    program = Program.objects.filter(pk=kwargs['pk'])
    view_display_name = 'program_delete_broadcast'
    
    if program:
        program = program[0]
    else: 
        print('Error in ' + view_display_name + ' view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()
    
    if not program.check_user_is_admin(request.user):
        print('Error in ' + view_display_name + ' view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden()
    
    selected_prefix = 'check-'
    check_counter = 0

    for key in request.POST.keys():
        
        if selected_prefix in key:
            check_counter+=1
            Broadcast.objects.filter(pk=request.POST.get(key)).delete()
        
    if check_counter==1:  
        messages.success(request,str(check_counter) + ' ' + _('station was successfully removed.'),extra_tags='edit')      
    elif check_counter > 1:
        messages.success(request,str(check_counter) + ' ' + _('stations were successfully removed.'),extra_tags='edit')
    else:
        messages.error(request, _('No program was selected. Please, check the program lines in order to commit the changes.'),
                       extra_tags='edit')                
    
    return HttpResponseRedirect(reverse('rss_feed:manage_program', args=(program.id,)))



class DeleteProgramPreview(generic.DetailView):
    
    model = Program
    template_name = 'rss_feed/predelete_program.html'
    
        
    def get_queryset_admins(self):
    
        return self.object.programadmin_set.order_by('user__username').prefetch_related('user')
    
        
    def get_context_data(self, **kwargs):
        
        context = super(DeleteProgramPreview, self).get_context_data(**kwargs)
        context['admin_list'] = self.get_queryset_admins()
        context['is_owner'] = self.object.check_user_is_admin(self.request.user,ADMT_OWNER[0])
        context['permissions_available'] = dict(EXISTING_ADMIN_TYPES)
        context['owner_permissions'] = ADMT_OWNER
        
        return context
    
    
    def get(self, request, **kwargs):
        
        if self.request.user.is_authenticated():
        
            self.object = self.get_object()
        
            if self.object.check_user_is_admin(self.request.user):
                
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)  
             
        return HttpResponseForbidden()    


@login_required
def delete_program(request,**kwargs):
    
    program = Program.objects.filter(pk=kwargs['pk'])
    view_display_name = 'delete_program'
    
    if program:
        program = program[0]
    else: 
        print('Error in ' + view_display_name + ' view, unknown station pk ' + str(kwargs['pk']))
        return HttpResponseNotFound()    
    
    if not program.check_user_is_admin(request.user,ADMT_OWNER[0]):
        print('Error in ' + view_display_name + ' view, user ' + str(request.user.id) + '-' + str(request.user.username) + 
              ' has no permissions to edit')
        return HttpResponseForbidden() 
    
    if request.method == 'POST':
    
        program.delete()
        return HttpResponseRedirect(reverse('rss_feed:deleted', args=()))


def define_search_tool(request):
    
    search_form = TextSearchForm()
    
    return {
        'search_form': search_form
    }

  
    
def search(request):
    
    if request.method == 'GET':

        form = TextSearchForm(request.GET)
        epage = request.GET.get('epage')
        ppage = request.GET.get('ppage')
        spage = request.GET.get('spage')
        upage = request.GET.get('upage')
        tag = request.GET.get('tag')
        tag_search = False
        
        if form.is_valid():
            
            raw_string = form.cleaned_data.get('text')
            word_list = raw_string.split(' ')
            request.session['search_wordlist'] = word_list
        
        else:
            
            if tag :
                word_list = [tag]
                tag_search = True
            else:
                word_list = request.session['search_wordlist']
                
            
        return render(request, 'rss_feed/search_results.html', {'episodes': textbox_search_episode(word_list,epage,tag_search),
                                                                'programs':textbox_search_program(word_list,ppage,tag_search),
                                                                'stations':textbox_search_station(word_list,spage),
                                                                'users':textbox_search_user(word_list,upage),
                                                                'all_tags':get_tag_cloud(40),
                                                                'keywords': ' '.join(word_list)})         
        
    return HttpResponseNotFound()   
        


def download(request):
    
    ep_id = None
    if request.method == 'GET':
        ep_id = request.GET['episode_id']

    downloads = 0
    
    if ep_id:
        
        already_downloaded = False
        try:
            listened_ep = list(request.session['listened_episodes'])
        except KeyError:
            listened_ep = []
        
        if ep_id in listened_ep:
            already_downloaded = True  
        
        ep = Episode.objects.get(id=int(ep_id))
        
        if ep:
            
            if already_downloaded:
                return HttpResponse(ep.downloads)
            
            downloads = ep.downloads + 1
            ep.downloads =  downloads
            ep.save()
            listened_ep.append(ep_id)
            request.session['listened_episodes'] = listened_ep
            
    return HttpResponse(downloads)


