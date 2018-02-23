'''
Created on 20 Feb 2018

@author: fer
'''

from django.utils import timezone
from django.core.files import File
from .models import Episode, Program, Image
from .models import ML_AUTHOR,ML_DESCRIPTION,ML_TITLE,ML_NAME
from .models import IVOOX_TYPE,RADIOCO_TYPE,PODOMATIC_TYPE
from datetime import datetime
import feedparser
import pytz
import urllib
import os


def truncate_strings(desc_string,max_len):
 
    if len(desc_string) > max_len:
        return desc_string[:max_len-2] + '..'
    
    return desc_string


def get_parser_by_program(a_program):
    
    if a_program.rss_link_type == IVOOX_TYPE[0]:
        return ParserIvoox(a_program.rss_link)
    
    if a_program.rss_link_type == RADIOCO_TYPE[0]:
        return ParserRadioco(a_program.rss_link)
    
    if a_program.rss_link_type == PODOMATIC_TYPE[0]:
        return ParserPodomatic(a_program.rss_link)

    else:
        print('No known parser')
        return None


class RSSLinkParser(object):
    
    
    def __init__(self,rss_link):
        
        self._link = rss_link  
        #self._image_dir = ABSOLUTE_IMAGE_DIR 
        
    
    def getLinkToAudio(self,dict_list):
        
        for a_dict in dict_list:
            
            try:
                if 'audio' in a_dict['type'] or 'video' in a_dict['type']:
                    return (a_dict['href'],a_dict['type']) 
                
            except KeyError:
                pass
            
        return None,None

    
    def process_episode_date(self,a_time_struct):
        
        return datetime(a_time_struct.tm_year,a_time_struct.tm_mon,a_time_struct.tm_mday,a_time_struct.tm_hour,
                        a_time_struct.tm_min,a_time_struct.tm_sec,0,tzinfo=pytz.UTC)
    

    def create_image(self,image_url):
        
        creation_date = timezone.now()
        original_image_name = os.path.basename(image_url)
        image_name = creation_date.strftime("%d%H%M%S") + '-' + original_image_name.lower()
        
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent','Mozilla/5.0')]
        urllib.request.install_opener(opener)
        image_file = urllib.request.urlretrieve(image_url)
        
        with open(image_file[0],'rb') as ifd: 
            
            new_image_instance = Image()
            new_image_instance.path.save( image_name, File(ifd) )
        
            new_image_instance.creation_date = creation_date
            new_image_instance.name = original_image_name
            new_image_instance.alt_text = original_image_name.lower()
            new_image_instance.original_url = image_url
            
            new_image_instance.save()
        
        return new_image_instance
            
    
    def get_program_image_url_from_feed_dict(self,feed_dict):
        
        return feed_dict['feed']['image']['href']
    
    
    def get_entry_list(self,feed_dict):
    
        return feed_dict['entries']
    
    
    def parse_program(self,feed_dict,disable_image_creation=False):
        
        pass
    
    
    def parse_episode(self,entry_dict,a_program):
        
        pass
    

    def parse_and_save(self):
        
        feed_dict = feedparser.parse(self._link.strip())
        new_program = self.parse_program(feed_dict)
        
        if new_program == None:   
            return False
        
        new_program.save()
        
        entry_list = self.get_entry_list(feed_dict)
        
        for an_entry in entry_list:
    
            self.parse_episode(an_entry, new_program).save()
        
        return True
 
 
 
class ParserIvoox(RSSLinkParser): 
        
    
    def parse_program(self,feed_dict,disable_image_creation=False):

        new_program = Program()
        
        try:
        
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
            new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.rss_link_type = IVOOX_TYPE[0]
            new_program.creation_date = timezone.now()
            new_program.original_site = feed_dict['feed']['link']
            
            if not disable_image_creation:
                new_program.image = self.create_image(self.get_program_image_url_from_feed_dict(feed_dict))
            
            return new_program
        
        except KeyError:
            
            return None


    def parse_episode(self,entry_dict,a_program):

        new_episode = Episode()
        new_episode.program = a_program

        new_episode.title = truncate_strings(entry_dict['title'],ML_TITLE)
        new_episode.summary = truncate_strings(entry_dict['summary'],ML_DESCRIPTION)
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        new_episode.original_id = entry_dict['id']
        new_episode.original_site = entry_dict['link']
        new_episode.image = Image.get_default_program_image()
        
        return new_episode
    
    


class ParserRadioco(RSSLinkParser):
    

    def parse_program(self,feed_dict,disable_image_creation=False):

        new_program = Program()

        try:
            
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = None
            new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.rss_link_type = RADIOCO_TYPE[0]
            new_program.creation_date = timezone.now()
            new_program.original_site = feed_dict['feed']['link']
            
            if not disable_image_creation:
                new_program.image = self.create_image(self.get_program_image_url_from_feed_dict(feed_dict))
            
            return new_program
            
        except KeyError:
            
            return None

    
    def parse_episode(self,entry_dict,a_program):
        
        
        new_episode = Episode()
        new_episode.program = a_program
        
        new_episode.title = truncate_strings(entry_dict['title'],ML_TITLE)
        new_episode.summary = truncate_strings(entry_dict['summary'],ML_DESCRIPTION)
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        # No original id in Radioco feeds
        new_episode.original_site = entry_dict['link']
        new_episode.image = Image.get_default_program_image()
        
        return new_episode
    


class ParserPodomatic(RSSLinkParser):


    def parse_program(self,feed_dict,disable_image_creation=False):
        
        new_program = Program()
        
        try:
        
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
            new_program.description = truncate_strings(feed_dict['feed']['summary'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.rss_link_type = PODOMATIC_TYPE[0]
            new_program.creation_date = timezone.now()
            new_program.original_site = feed_dict['feed']['link']
            
            if not disable_image_creation:
                new_program.image = self.create_image(self.get_program_image_url_from_feed_dict(feed_dict))
    
            
            return new_program
            
        except KeyError:
            
            return None
    
    
    def parse_episode(self,entry_dict,a_program):
        
        new_episode = Episode()
        
        new_episode.program = a_program        
        new_episode.title = truncate_strings(entry_dict['title'],ML_TITLE)
        new_episode.summary = truncate_strings(entry_dict['content'][0]['value'],ML_DESCRIPTION)
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        new_episode.original_id = entry_dict['id']
        new_episode.original_site = entry_dict['link']
        
        try:
            new_episode.image = self.create_image(entry_dict['image']['href'])
        except:
            print('Episode ' + new_episode.title + ' No image file found. Setting default instead')
            new_episode.image = Image.get_default_program_image()
    
        return new_episode
        


    
    
    