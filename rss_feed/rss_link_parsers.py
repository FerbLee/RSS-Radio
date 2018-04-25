'''
Created on 20 Feb 2018

@author: fer
'''

from django.utils import timezone
from django.core.files import File
from .models import Episode, Program, Image, Tag
from .models import IVOOX_TYPE,RADIOCO_TYPE,PODOMATIC_TYPE,ADMT_OWNER
from datetime import datetime
import feedparser
import pytz
import urllib
import os


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


def create_image(image_url):
    
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


def get_tag_instance(name):
    
    clean_name = Tag.clean_name(name)

    tag_instance = Tag.objects.filter(name=clean_name)

    if tag_instance.exists():
        
        tag_instance = tag_instance[0]
        tag_instance.times_used += 1
    
    else:
        
        tag_instance = Tag(name=clean_name)

    tag_instance.save()

    return tag_instance



class RSSLinkParser(object):
    
    
    def __init__(self,rss_link,owner=None):
        
        self._link = rss_link  
        self._owner = owner
    
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
       
    
    def get_program_image_url_from_feed_dict(self,feed_dict):
        
        return feed_dict['feed']['image']['href']
    
    
    def get_episode_image_url_from_entry_dict(self,entry_dict):
    
        # WARNING: Can raise KeyError in any parser
        return entry_dict['image']['href']
            
    
    def get_program_tag_names_from_feed_dict(self,feed_dict,clean=False):
    
        if clean:
            return [Tag.clean_name(tag_dict['term']) for tag_dict in feed_dict['feed']['tags']]
        else:
            return [tag_dict['term'] for tag_dict in feed_dict['feed']['tags']]


    def get_episode_tag_names_from_entry_dict(self,entry_dict,clean=False):
    
        try:
            
            if clean:
            
                return [Tag.clean_name(tag_dict['term']) for tag_dict in entry_dict['tags']]
            
            else:
            
                return [tag_dict['term'] for tag_dict in entry_dict['tags']]
        
        except KeyError:
            
            return []
            
    
    def get_entry_list(self,feed_dict):
    
        return feed_dict['entries']
    
    
    def parse_program(self,feed_dict,disable_image_creation=False):
        
        pass
    
    
    def parse_episode(self,entry_dict,a_program):
        
        pass
    
    
    def save_single_episode(self,entry_dict,program):
        
        # parse_episode - raises key error  
        new_episode = self.parse_episode(entry_dict, program)
        
        try:
            
            image_url = self.get_episode_image_url_from_entry_dict(entry_dict)
            new_episode.image = create_image(image_url)
        
        except KeyError:
        
            #new_episode.image = Image.get_default_program_image()
            new_episode.image = program.image
        
        new_episode.save()
    
        episode_tag_list = self.get_episode_tag_names_from_entry_dict(entry_dict,clean=True)
        
        for tag_name in episode_tag_list:
        
            tag_instance = get_tag_instance(tag_name)
            tag_instance.episodes.add(new_episode) 
        
        return new_episode
        

    def parse_and_save(self):
        
        # 1. Get dictionary from rss_link
        feed_dict = feedparser.parse(self._link.strip())
        
        try:
            # 2. Create new program instance
            new_program = self.parse_program(feed_dict)
            # 3. Create image instance and add to program
            new_program.image = create_image(self.get_program_image_url_from_feed_dict(feed_dict))
        
        except KeyError:
            
            return False
        
        # 4.Save program
        new_program.save()
        
        
        # Add owner
        new_program.programadmin_set.create(user=self._owner,type=ADMT_OWNER[0])
        
        
        # 5. Create/Get tag instances and add them to program
        program_tag_list = self.get_program_tag_names_from_feed_dict(feed_dict)
        
        for tag_name in program_tag_list:
            
            tag_instance = get_tag_instance(tag_name)
            tag_instance.programs.add(new_program) 
        
        
        # 6. Get episodes
        entry_list = self.get_entry_list(feed_dict)
        
        for entry_dict in entry_list:
    
            try:
                self.save_single_episode(entry_dict,new_program)
            except KeyError:
                continue
            
        return True
 
 
 
class ParserIvoox(RSSLinkParser): 
    
    # Overrides superclass method.
    def get_episode_tag_names_from_entry_dict(self,_,clean=False):
    
        # No tags in episode entry for this feed type
        return []
    
    
    def parse_program(self,feed_dict):

        new_program = Program()
        
        new_program.name = feed_dict['feed']['title']
        new_program.author = feed_dict['feed']['author']
        new_program.description = feed_dict['feed']['subtitle']
        new_program.rss_link = self._link
        new_program.rss_link_type = IVOOX_TYPE[0]
        new_program.creation_date = timezone.now()
        new_program.original_site = feed_dict['feed']['link']
        
        new_program.language = feed_dict['feed']['language']
        
        for auth_item in feed_dict['feed']['authors']:
            
            try:
                new_program.author_email = auth_item['email']
            except KeyError:
                pass
        
        return new_program


    def parse_episode(self,entry_dict,a_program):

        new_episode = Episode()
        new_episode.program = a_program

        new_episode.title = entry_dict['title']
        new_episode.summary = entry_dict['summary']
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        new_episode.original_id = entry_dict['id']
        new_episode.original_site = entry_dict['link']
        
        return new_episode
    
    


class ParserRadioco(RSSLinkParser):
    
    # Overrides superclass method.
    def get_episode_tag_names_from_entry_dict(self,_,clean=False):
    
        # No tags in episode entry for this feed type
        return []
    

    def parse_program(self,feed_dict):

        new_program = Program()

        new_program.name = feed_dict['feed']['title']
        new_program.author = None
        new_program.description = feed_dict['feed']['subtitle']
        new_program.rss_link = self._link
        new_program.rss_link_type = RADIOCO_TYPE[0]
        new_program.creation_date = timezone.now()
        new_program.original_site = feed_dict['feed']['link']
        new_program.language = feed_dict['feed']['language']
       
        return new_program
             

    
    def parse_episode(self,entry_dict,a_program):
        
        
        new_episode = Episode()
        new_episode.program = a_program
        
        new_episode.title = entry_dict['title']
        new_episode.summary = entry_dict['summary']
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        # No original id in Radioco feeds
        new_episode.original_site = entry_dict['link']
        
        return new_episode
    


class ParserPodomatic(RSSLinkParser):


    def parse_program(self,feed_dict):
        
        new_program = Program()
        
        new_program.name = feed_dict['feed']['title']
        new_program.author = feed_dict['feed']['author']
        new_program.language = feed_dict['feed']['language']
        
        for auth_item in feed_dict['feed']['authors']:
            
            try:
                new_program.author_email = auth_item['email']
            except KeyError:
                pass
             
        new_program.description = feed_dict['feed']['summary']
        new_program.rss_link = self._link
        new_program.rss_link_type = PODOMATIC_TYPE[0]
        new_program.creation_date = timezone.now()
        new_program.original_site = feed_dict['feed']['link']
        
        return new_program
    
    
    def parse_episode(self,entry_dict,a_program):
        
        new_episode = Episode()
        
        new_episode.program = a_program        
        new_episode.title = entry_dict['title']
        new_episode.summary = entry_dict['content'][0]['value']
        new_episode.publication_date = self.process_episode_date(entry_dict['published_parsed'])
        new_episode.file,new_episode.file_type = self.getLinkToAudio(entry_dict['links'])
        new_episode.insertion_date = timezone.now()
        new_episode.original_id = entry_dict['id']
        new_episode.original_site = entry_dict['link']
    
        return new_episode
        


    
    
    