'''
Created on 20 Feb 2018

@author: fer
'''

from django.utils import timezone
from .models import Episode, Program
from .models import ML_AUTHOR,ML_DESCRIPTION,ML_TITLE,ML_NAME
from datetime import datetime
import feedparser
import calendar
import pytz

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
                if 'audio' in a_dict['type'] or 'video' in a_dict['type']:
                    return (a_dict['href'],a_dict['type']) 
                
            except KeyError:
                pass
            
        return None,None

    
    def process_episode_date(self,a_time_struct):
        
        return datetime(a_time_struct.tm_year,a_time_struct.tm_mon,a_time_struct.tm_mday,a_time_struct.tm_hour,a_time_struct.tm_min,a_time_struct.tm_sec,0,tzinfo=pytz.UTC)
    


    def parse_and_save(self):
        
        pass
 
 
 
class ParserIvoox(RSSLinkParser): 


    def parse_and_save(self):
        
        print('Ivoox')
        feed_dict = feedparser.parse(self._link.strip())
        new_program = Program()
        
        try:
        
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
            new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.creation_date = timezone.now()
        
        except KeyError:
            
            return False
        
        new_program.save()
        
        for an_entry in feed_dict['entries']:
    
            new_episode = Episode()
            new_episode.program = new_program
    
            new_episode.title = truncate_strings(an_entry['title'],ML_TITLE)
            new_episode.summary = truncate_strings(an_entry['summary'],ML_DESCRIPTION)
            new_episode.publication_date = self.process_episode_date(an_entry['published_parsed'])
            new_episode.file,new_episode.file_type = self.getLinkToAudio(an_entry['links'])
    
            new_episode.save()
        
        return True


class ParserRadioco(RSSLinkParser):


    def parse_and_save(self):
        
        print('RADIOCO')
        feed_dict = feedparser.parse(self._link.strip())
        new_program = Program()
        
        try:
            
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = None
            new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.creation_date = timezone.now()
            
        except KeyError:
            
            return False
        
        new_program.save()
    
        for an_entry in feed_dict['entries']:
            
            new_episode = Episode()
            new_episode.program = new_program
            
            new_episode.title = truncate_strings(an_entry['title'],ML_TITLE)
            new_episode.summary = truncate_strings(an_entry['summary'],ML_DESCRIPTION)
            new_episode.publication_date = self.process_episode_date(an_entry['published_parsed'])
            new_episode.file,new_episode.file_type = self.getLinkToAudio(an_entry['links'])
            
            new_episode.save()
    
        return True


class ParserPodomatic(RSSLinkParser):


    def parse_and_save(self):
        
        print('Podomatic')
        feed_dict = feedparser.parse(self._link.strip())
        new_program = Program()
        
        try:
        
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
            new_program.description = truncate_strings(feed_dict['feed']['summary'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.creation_date = timezone.now()
    
        except KeyError:
            
            return False
        
        new_program.save()
        
        for an_entry in feed_dict['entries']:
    
            new_episode = Episode()
            new_episode.program = new_program
                    
            new_episode.title = truncate_strings(an_entry['title'],ML_TITLE)
            
            new_episode.summary = truncate_strings(an_entry['content'][0]['value'],ML_DESCRIPTION)
       
            new_episode.publication_date = self.process_episode_date(an_entry['published_parsed'])
            new_episode.file,new_episode.file_type = self.getLinkToAudio(an_entry['links'])
            
            if new_episode.file != None:
                new_episode.save()
            else:
                print('Episode ' + new_episode.title + ' NOT saved: No audio file found.')
        
        return True
    
    
    