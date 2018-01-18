from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
import feedparser
import time
from .models import Episodio, Programa
from .models import MAX_LENGTH_DESCRIPTIONS as mld


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


def getLinkToAudio(dict_list):
    
    for a_dict in dict_list:
        
        try:
            if 'audio' in a_dict['type']:
                return a_dict['href'] 
        
        except KeyError:
            pass
        
    return None
        

def addLinkIvoox(link):
    
    print('Ivoox')
    feed_dict = feedparser.parse(link.strip())
    novo_programa = Programa()
    
    try:
    
        novo_programa.nome = feed_dict['feed']['title']
        novo_programa.autor = feed_dict['feed']['author']
        novo_programa.descricion = feed_dict['feed']['subtitle']
        novo_programa.rss_link = link
    
    except KeyError:
        
        return False
    
    novo_programa.save()
    
    for an_entry in feed_dict['entries']:

        novo_episodio = Episodio()
        novo_episodio.programa = novo_programa
                
        try:

            novo_episodio.titulo = an_entry['title']
            novo_episodio.resumo = an_entry['summary']
            #novo_episodio.data_publicacion = iso = time.strftime('%Y-%M-%D %H:%M', an_entry['published_parsed'])
            novo_episodio.ficheiro = an_entry['link']
        
        except KeyError:
            
            return False
        
        novo_episodio.save()
    
    return True


def addLinkRadioco(link):

    print('RADIOCO')
    feed_dict = feedparser.parse(link.strip())
    novo_programa = Programa()
    
    try:
        
        novo_programa.nome = feed_dict['feed']['title']
        novo_programa.autor = None
        novo_programa.descricion = (feed_dict['feed']['subtitle'][:mld-2] + '..') if len(feed_dict['feed']['subtitle']) > mld else feed_dict['feed']['subtitle']
        novo_programa.rss_link = link
        
    except KeyError:
        
        return False
    
    novo_programa.save()

    for an_entry in feed_dict['entries']:
        
        novo_episodio = Episodio()
        novo_episodio.programa = novo_programa
        
        try:
        
            novo_episodio.titulo = an_entry['title']
            novo_episodio.resumo = (an_entry['summary'][:mld-2] + '..') if len(an_entry['summary']) > mld else an_entry['summary']
            #novo_episodio.data_publicacion = iso = time.strftime('%Y-%M-%D %H:%M', an_entry['published_parsed'])
            print (getLinkToAudio(an_entry['links']))
            novo_episodio.ficheiro = getLinkToAudio(an_entry['links'])
        
        except KeyError:
            
            return False
        
        novo_episodio.save()

    return True


def addLinkItunes(link):
    
    pass


def addLink(request):
    
    link = request.POST.get("rss_link")
    
    if addLinkIvoox(link):
        pass
    elif addLinkRadioco(link):
        pass
    else:         
        print("ERROR: Format Unknown")
                
    return HttpResponseRedirect(reverse('rss_feed:index', args=()))



