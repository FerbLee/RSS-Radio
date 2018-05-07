'''
Created on 4 May 2018

@author: fer
'''

from .models import Episode, Program, Image, Station, User
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

PAGE_SIZE = 8


def _aux_create_search_query(word_list):
    
    if word_list != []:
        
        query_or = SearchQuery(word_list[0])  
            
        for word in word_list[1:]:
            query_or = query_or |  SearchQuery(word) 
        
        return query_or

    raise IndexError
    

def _aux_paginator_creation(result_qs,page,ps=PAGE_SIZE):
    
    paginator = Paginator(result_qs, ps)
    
    try:
        return paginator.page(page)
        
    except PageNotAnInteger:
        return paginator.page(1)
    
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        return paginator.page(paginator.num_pages)
    


def textbox_search_episode(word_list,page=1):
    
    result_qs = Episode.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
            
        vector = SearchVector('title', 'summary')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank','-publication_date')

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)
        


def textbox_search_program(word_list,page=1):
    
    result_qs = Program.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
            
        vector = SearchVector('name', 'description')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank','-popularity')

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)
        


def textbox_search_station(word_list,page=1):
    
    result_qs = Station.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
            
        vector = SearchVector('name', 'description','location','broadcasting_area')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank')

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)


def textbox_search_user(word_list,page=1):
    
    result_qs = User.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
            
        vector = SearchVector('username','first_name','last_name','userprofile__description','userprofile__location','email')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank')

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)
    
    
    



