'''
Created on 20 Feb 2018

@author: fer
'''

from rss_feed.rss_link_parsers import get_parser_by_program
from rss_feed.models import Program, Episode
from rss_feed.models import PROGRAM_ATB_FROM_RSS
import feedparser


def ud_update_program(program_old,program_new,image_url_new,rss_parser):

    po_dict = program_old.__dict__
    pn_dict = program_new.__dict__
    
    it_keys = PROGRAM_ATB_FROM_RSS
    
    # Check updated attributes
    change = False
    for a_key in it_keys:
        
        if po_dict[a_key] != pn_dict[a_key]:
            
            po_dict[a_key] = pn_dict[a_key]
            change = True

    # Check updated image
    if program_old.image.original_url != image_url_new:
        
        new_image = rss_parser.create_image(image_url_new)
        program_old.image = rss_parser.create_image(new_image)
        change = True
    
    if change:
        print('Program ' + program_old.name + ' was UPDATED')
        program_old.save() 
    else:
        print('Program ' + program_old.name + ' nothing to do')
        


def ud_update_episode(episode_old,episode_new):

    pass


def ud_create_episode_rss():
    
    pass


def ud_iterate_episode_table(a_program,entry_list,rss_parser=None):
    
    if rss_parser == None:
        
        rss_parser = get_parser_by_program(a_program)
    
    for an_entry in entry_list:
        
        episode_new = rss_parser.parse_episode(an_entry,a_program)
        
        if episode_new.original_id != None:
            episode_old_qs = Episode.objects.filter(program_id=a_program,original_id=episode_new.original_id)
        else:
            episode_old_qs = Episode.objects.filter(program_id=a_program,title=episode_new.title,
                                                    original_site=episode_new.original_site)
        if episode_old_qs.exists():
            #Update_episode
            pass
        else:
            #Create_new_episode
            pass
        
        
        


def ud_iterate_program_table():
    
    program_set = Program.objects.all()

    # chunk size 2000 default cannot be changed
    for a_program in program_set.iterator():
        
        feed_dict = feedparser.parse(a_program.rss_link)
        
        parser = get_parser_by_program(a_program)
        
        updated_program = parser.parse_program(feed_dict,disable_image_creation=True)
        updated_image_url = parser.get_program_image_url_from_feed_dict(feed_dict)   
        
        ud_update_program(a_program,updated_program,updated_image_url,parser)
            
         
         

def main():

    ud_iterate_program_table()


if __name__ == '__main__':
    
    main()
    