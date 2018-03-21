from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Episode, Program, Image
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login
from .forms import SignUpForm 
from django.utils import timezone
from django.contrib.auth.models import User
import os

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


def create_avatar(avatar_url,username):

#    try:
        
    if avatar_url != None:
    
        avatar_img = Image()
        avatar_img.path = avatar_url
        avatar_img.creation_date = timezone.now()
        avatar_img.name = os.path.basename(avatar_url)
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

