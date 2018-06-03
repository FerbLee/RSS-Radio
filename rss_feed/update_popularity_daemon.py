'''
Created on 3 Jun 2018

@author: fer
'''
from rss_feed.models import Program, Episode
from django.utils import timezone
from datetime import timedelta


def program_popularity_formula(subs,stations,wgd_rating,listens):

    wgd_subs = 5*subs
    wgd_stations = 10*stations

    return wgd_subs + wgd_stations + wgd_rating + listens


def get_subscriptions(program):
    
    return program.subscribers.count()


def get_broadcasting_stations(program):
    
    return program.broadcast_set.count()

def update_pop_all_programs():
    
    program_set = Program.objects.all()

    # chunk size 2000 default cannot be changed
    for a_program in program_set.iterator():
        
        print('**************' + str(a_program))
        
        nof_subs = get_subscriptions(a_program)
        nof_stations = get_broadcasting_stations(a_program)
        
        rating = 0
        wgd_rating = 0
        listens = 0
        
        end_date = timezone.now()
        start_date =  end_date - timedelta(days=365)
        episode_set = a_program.episode_set.filter(publication_date__range=[start_date, end_date])
        
        for an_episode in episode_set.iterator():
            
            likes = an_episode.get_upvote_number()
            dislikes = an_episode.get_downvote_number()
            
            rating += likes - dislikes
            wgd_rating += (likes - dislikes) * (likes + dislikes)
            
            listens += an_episode.downloads
            
        print(program_popularity_formula(nof_subs,nof_stations,wgd_rating,listens))
        
        
        
        