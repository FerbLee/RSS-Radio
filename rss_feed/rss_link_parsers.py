'''
Created on 20 Feb 2018

@author: fer
'''

from .models import Episodio, Programa
from .models import ML_AUTOR,ML_DESCRICION,ML_TITULO,ML_NOME
import feedparser
import time


def truncate_strings(desc_string,max_len):
 
    if len(desc_string) > max_len:
        return desc_string[:max_len-2] + '..'
    
    return desc_string


class RSSLinkParser(object):
    
    
    def __init__(self,rss_link):
        
        self._link = rss_link  
    
    
    def getLinkToAudio(self,dict_list):
        
        for a_dict in dict_list:
            
            try:
                if 'audio' in a_dict['type']:
                    return a_dict['href'] 
            
            except KeyError:
                pass
            
        return None


    def parse_and_save(self):
        
        pass
 
 
 
class ParserIvoox(RSSLinkParser): 


    def parse_and_save(self):
        
        print('Ivoox')
        feed_dict = feedparser.parse(self._link.strip())
        novo_programa = Programa()
        
        try:
        
            novo_programa.nome = truncate_strings(feed_dict['feed']['title'],ML_NOME)
            novo_programa.autor = truncate_strings(feed_dict['feed']['author'],ML_AUTOR)
            novo_programa.descricion = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRICION)
            novo_programa.rss_link = self._link
        
        except KeyError:
            
            return False
        
        novo_programa.save()
        
        for an_entry in feed_dict['entries']:
    
            novo_episodio = Episodio()
            novo_episodio.programa = novo_programa
    
            novo_episodio.titulo = truncate_strings(an_entry['title'],ML_TITULO)
            novo_episodio.resumo = truncate_strings(an_entry['summary'],ML_DESCRICION)
            #novo_episodio.data_publicacion = iso = time.strftime('%Y-%M-%D %H:%M', an_entry['published_parsed'])
            novo_episodio.ficheiro = self.getLinkToAudio(an_entry['links'])
    
            novo_episodio.save()
        
        return True


class ParserRadioco(RSSLinkParser):


    def parse_and_save(self):
        
        print('RADIOCO')
        feed_dict = feedparser.parse(self._link.strip())
        novo_programa = Programa()
        
        try:
            
            novo_programa.nome = truncate_strings(feed_dict['feed']['title'],ML_NOME)
            novo_programa.autor = None
            novo_programa.descricion = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRICION)
            novo_programa.rss_link = self._link
            
        except KeyError:
            
            return False
        
        novo_programa.save()
    
        for an_entry in feed_dict['entries']:
            
            novo_episodio = Episodio()
            novo_episodio.programa = novo_programa
            
            novo_episodio.titulo = truncate_strings(an_entry['title'],ML_TITULO)
            novo_episodio.resumo = truncate_strings(an_entry['summary'],ML_DESCRICION)
            #novo_episodio.data_publicacion = iso = time.strftime('%Y-%M-%D %H:%M', an_entry['published_parsed'])
            novo_episodio.ficheiro = self._getLinkToAudio(an_entry['links'])
            
            
            novo_episodio.save()
    
        return True


class ParserPodomatic(RSSLinkParser):


    def parse_and_save(self):
        
        print('Podomatic')
        feed_dict = feedparser.parse(self._link.strip())
        novo_programa = Programa()
        
        try:
        
            novo_programa.nome = truncate_strings(feed_dict['feed']['title'],ML_NOME)
            novo_programa.autor = truncate_strings(feed_dict['feed']['author'],ML_AUTOR)
            novo_programa.descricion = truncate_strings(feed_dict['feed']['summary'],ML_DESCRICION)
            novo_programa.rss_link = self._link
    
        except KeyError:
            
            return False
        
        novo_programa.save()
        
        for an_entry in feed_dict['entries']:
    
            novo_episodio = Episodio()
            novo_episodio.programa = novo_programa
                    
            novo_episodio.titulo = truncate_strings(an_entry['title'],ML_TITULO)
            
            try:
                novo_episodio.resumo = truncate_strings(an_entry['content'][0]['value'],ML_DESCRICION)
            except IndexError:
                novo_episodio.resumo = ''
            #novo_episodio.data_publicacion = iso = time.strftime('%Y-%M-%D %H:%M', an_entry['published_parsed'])
            novo_episodio.ficheiro = self.getLinkToAudio(an_entry['links'])
        
            
            novo_episodio.save()
        
        return True