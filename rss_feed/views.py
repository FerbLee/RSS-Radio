from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Episode, Program
from rss_feed import rss_link_parsers as rlp 
from django.contrib.auth import authenticate, login


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


