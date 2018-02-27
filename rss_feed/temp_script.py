'''
Created on 20 Feb 2018

@author: fer
'''

from rss_feed.rss_link_parsers import get_parser_by_program, create_image, get_tag_instance
from rss_feed.models import Program, Episode
from rss_feed.models import PROGRAM_ATB_FROM_RSS,EPISODE_ATB_FROM_RSS
import feedparser


def ud_update_tags(entity_old,new_tags_name_list):

    old_tags = entity_old.tag_set.all()
    new_tags_name_set = set(new_tags_name_list)
    change = False
    
    for a_tag in old_tags:
      
        if a_tag.name not in new_tags_name_set:
            
            print(a_tag.name)
            a_tag.programs.remove(entity_old)
            a_tag.times_used -= 1
            a_tag.save()
            change = True
        
        else:
            
            new_tags_name_set.remove(a_tag.name)
            
    for tag_name in new_tags_name_set:
        
        a_tag = get_tag_instance(tag_name)
        a_tag.programs.add(entity_old)
        change = True
    
    return change
    



def ud_update_program_episode(entity_old,entity_new,it_keys,image_url_new,tags_name_list):

    eo_dict = entity_old.__dict__
    en_dict = entity_new.__dict__
    
    #it_keys = PROGRAM_ATB_FROM_RSS
    
    # Check update attributes
    change = False
    for a_key in it_keys:
        
        if eo_dict[a_key] != en_dict[a_key]:
            
            eo_dict[a_key] = en_dict[a_key]
            change = True

    # Check updated image
    if entity_old.image.original_url != image_url_new:
        
        entity_old.image = create_image(image_url_new)
        change = True
    
    # Save attributes if changed
    if change:
        entity_old.save() 
        print(str(type(entity_old)) + ' ' + entity_old.name + ' attributes UPDATED')
        
    # Check update tags (needs to be done after saving due to many-to-many rel)
    change_tags = ud_update_tags(entity_old,tags_name_list)
        
    if change_tags:
        print(str(type(entity_old)) + ' ' + entity_old.name + ' tags UPDATED')
        
    elif not (change or change_tags):
        print('Program ' + entity_old.name + ' nothing to do')



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
        
        updated_program = parser.parse_program(feed_dict)
        updated_image_url = parser.get_program_image_url_from_feed_dict(feed_dict)   
        updated_tag_names = parser.get_program_tag_names_from_feed_dict(feed_dict,clean=True)
        
        ud_update_program_episode(a_program,updated_program,PROGRAM_ATB_FROM_RSS,updated_image_url,updated_tag_names)
            
         
         

def main():

    ud_iterate_program_table()


if __name__ == '__main__':
    
    main()
    