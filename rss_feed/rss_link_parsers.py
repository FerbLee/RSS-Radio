'''
Created on 20 Feb 2018

@author: fer
'''

from django.utils import timezone
from django.core.files import File
from .models import Episode, Program, Image, Tag
from .models import ML_AUTHOR,ML_DESCRIPTION,ML_TITLE,ML_NAME
from .models import IVOOX_TYPE,RADIOCO_TYPE,PODOMATIC_TYPE
from datetime import datetime
import feedparser
import pytz
import urllib
import os
from django.utils.timezone import override


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
    
    
    def get_tag_instance(self,name):
        
        clean_name = name.lower().strip()
    
        tag_instance = Tag.objects.filter(name=clean_name)

        if tag_instance.exists():
            
            tag_instance = tag_instance[0]
            tag_instance.times_used += 1
        
        else:
            
            tag_instance = Tag(name=clean_name)
 
        tag_instance.save()
 
        return tag_instance
    
    
    
    def get_program_image_url_from_feed_dict(self,feed_dict):
        
        return feed_dict['feed']['image']['href']
    
    
    def get_episode_image_url_from_entry_dict(self,entry_dict):
    
        # WARNING: Can raise KeyError in any parser
        return entry_dict['image']['href']
            
    
    def get_program_tag_names_from_feed_dict(self,feed_dict):
    
        return [tag_dict['term'] for tag_dict in feed_dict['feed']['tags']]


    def get_episode_tag_names_from_entry_dict(self,entry_dict):
    
        try:
            
            return [tag_dict['term'] for tag_dict in entry_dict['tags']]
        
        except KeyError:
            
            return []
            
    
    def get_entry_list(self,feed_dict):
    
        return feed_dict['entries']
    
    
    def parse_program(self,feed_dict,disable_image_creation=False):
        
        pass
    
    
    def parse_episode(self,entry_dict,a_program):
        
        pass
    

    def parse_and_save(self):
        
        # 1. Get dictionary from rss_link
        feed_dict = feedparser.parse(self._link.strip())
        
        try:
            # 2. Create new program instance
            new_program = self.parse_program(feed_dict)
            # 3. Create image instance and add to program
            new_program.image = self.create_image(self.get_program_image_url_from_feed_dict(feed_dict))
        
        except KeyError:
            
            return False
        
        # 4. Save program
        new_program.save()
        
        # 5. Create/Get tag instances and add them to program
        program_tag_list = self.get_program_tag_names_from_feed_dict(feed_dict)
        
        for tag_name in program_tag_list:
            
            tag_instance = self.get_tag_instance(tag_name)
            tag_instance.programs.add(new_program) 
        
        
        # 6. Get episodes
        entry_list = self.get_entry_list(feed_dict)
        
        for entry_dict in entry_list:
    
            try:
                new_episode = self.parse_episode(entry_dict, new_program)
            except KeyError:
                continue
            
            try:
                
                image_url = self.get_episode_image_url_from_entry_dict(entry_dict)
                new_episode.image = self.create_image(image_url)
            
            except KeyError:
            
                new_episode.image = Image.get_default_program_image()
            
            new_episode.save()
        
            episode_tag_list = self.get_episode_tag_names_from_entry_dict(entry_dict)
            
            for tag_name in episode_tag_list:
            
                tag_instance = self.get_tag_instance(tag_name)
                tag_instance.episodes.add(new_episode) 
        
        
        return True
 
 
 
class ParserIvoox(RSSLinkParser): 
    
    # Overrides superclass method.
    def get_episode_tag_names_from_entry_dict(self,_):
    
        # No tags in episode entry for this feed type
        return []
    
    
    def parse_program(self,feed_dict):

        new_program = Program()
        
        new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
        new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
        new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
        new_program.rss_link = self._link
        new_program.rss_link_type = IVOOX_TYPE[0]
        new_program.creation_date = timezone.now()
        new_program.original_site = feed_dict['feed']['link']
        
        return new_program


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
        
        return new_episode
    
    


class ParserRadioco(RSSLinkParser):
    
    # Overrides superclass method.
    def get_episode_tag_names_from_entry_dict(self,_):
    
        # No tags in episode entry for this feed type
        return []
    

    def parse_program(self,feed_dict):

        new_program = Program()

        try:
            
            new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
            new_program.author = None
            new_program.description = truncate_strings(feed_dict['feed']['subtitle'],ML_DESCRIPTION)
            new_program.rss_link = self._link
            new_program.rss_link_type = RADIOCO_TYPE[0]
            new_program.creation_date = timezone.now()
            new_program.original_site = feed_dict['feed']['link']
            
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
        
        return new_episode
    


class ParserPodomatic(RSSLinkParser):


    def parse_program(self,feed_dict,disable_image_creation=False):
        
        new_program = Program()
        
        new_program.name = truncate_strings(feed_dict['feed']['title'],ML_NAME)
        new_program.author = truncate_strings(feed_dict['feed']['author'],ML_AUTHOR)
        new_program.description = truncate_strings(feed_dict['feed']['summary'],ML_DESCRIPTION)
        new_program.rss_link = self._link
        new_program.rss_link_type = PODOMATIC_TYPE[0]
        new_program.creation_date = timezone.now()
        new_program.original_site = feed_dict['feed']['link']
        
        return new_program
    
    
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
    
        return new_episode
        


    
    
    