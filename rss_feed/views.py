from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Episodio, Programa
from rss_feed import rss_link_parsers as rlp 


class IndexView(generic.ListView):
    
    template_name = 'rss_feed/index.html'
    context_object_name = 'lista_programas'

    def get_queryset(self):
        
        """Listado de Programas engadidos"""
        return Programa.objects.all()


class ProgramaDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Programa
    template_name = 'rss_feed/detail_programa.html'

        

class EpisodioDetailView(generic.DetailView):
    
    #Overrides model and template_name from superclass
    model = Episodio
    template_name = 'rss_feed/detail_episodio.html'




def addLink(request):
    
    link = request.POST.get("rss_link")
    
    known_parsers = {'podomatic':rlp.ParserPodomatic(link),'ivoox':rlp.ParserIvoox(link),
                     'radioco':rlp.ParserRadioco(link)}
    
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



