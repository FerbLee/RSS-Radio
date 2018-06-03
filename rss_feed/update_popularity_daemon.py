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


def program_rating_formula(likes,dislikes):

    if (likes+dislikes) > 0:
        
        return 100*likes/(likes + dislikes)

    return 50

def episode_wgd_rating_formula(likes,dislikes):

    return (likes - dislikes) * (likes + dislikes)

def get_subscriptions(program):
    
    return program.subscribers.count()


def get_broadcasting_stations(program):
    
    return program.broadcast_set.count()

def update_pop_rating_all_programs():
    
    program_set = Program.objects.all()

    # chunk size 2000 default cannot be changed
    for a_program in program_set.iterator():
        
        nof_subs = get_subscriptions(a_program)
        nof_stations = get_broadcasting_stations(a_program)
        
        total_likes = 0
        total_dislikes = 0
        wgd_rating = 0
        listens = 0
        
        end_date = timezone.now()
        start_date =  end_date - timedelta(days=365)
        episode_set = a_program.episode_set.filter(publication_date__range=[start_date, end_date])
        
        for an_episode in episode_set.iterator():
            
            likes = an_episode.get_upvote_number()
            dislikes = an_episode.get_downvote_number()
            
            total_likes += likes
            total_dislikes += dislikes
            
            wgd_rating += episode_wgd_rating_formula(likes,dislikes)
            
            listens += an_episode.downloads
            

        a_program.popularity = program_popularity_formula(nof_subs,nof_stations,wgd_rating,listens)
        a_program.rating = program_rating_formula(total_likes,total_dislikes)
        
        a_program.save()
        print(str(a_program.name) + ' Popularity:' + str(a_program.popularity) + ' Rating:' + str(a_program.rating) )
        
        