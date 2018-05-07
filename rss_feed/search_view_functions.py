'''
Created on 4 May 2018

@author: fer
'''

from .models import Episode, Program, Image, Station, User
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank


def _aux_create_search_query(word_list):
    
    if word_list != []:
        
        query_or = SearchQuery(word_list[0])  
            
        for word in word_list[1:]:
            query_or = query_or |  SearchQuery(word) 
        
        return query_or

    raise IndexError
    


def textbox_search_episode(word_list):
    
    result_qs = Episode.objects.all()
    
    try:
        query_or = _aux_create_search_query(word_list)
    except IndexError:
        return result_qs
        
    vector = SearchVector('title', 'summary')
    
    qs_or = result_qs.annotate(search=vector).filter(search=query_or)
    qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
    
    result_qs = qs_or.order_by('-rank','-publication_date')

    return result_qs
        


def textbox_search_program(word_list):
    
    result_qs = Program.objects.all()
    
    try:
        query_or = _aux_create_search_query(word_list)
    except IndexError:
        return result_qs
        
    vector = SearchVector('name', 'description')
    
    qs_or = result_qs.annotate(search=vector).filter(search=query_or)
    qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
    
    result_qs = qs_or.order_by('-rank','-popularity')

    return result_qs


def textbox_search_station(word_list):
    
    result_qs = Station.objects.all()
    
    try:
        query_or = _aux_create_search_query(word_list)
    except IndexError:
        return result_qs
        
    vector = SearchVector('name', 'description', 'location')
    
    qs_or = result_qs.annotate(search=vector).filter(search=query_or)
    qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
    
    result_qs = qs_or.order_by('-rank')

    return result_qs


def textbox_search_user(word_list):
    
    result_qs = User.objects.all()
    
    try:
        query_or = _aux_create_search_query(word_list)
    except IndexError:
        return result_qs
        
    vector = SearchVector('username','first_name','last_name','userprofile__description','userprofile__location','email')
    
    qs_or = result_qs.annotate(search=vector).filter(search=query_or)
    qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
    
    result_qs = qs_or.order_by('-rank')

    return result_qs



