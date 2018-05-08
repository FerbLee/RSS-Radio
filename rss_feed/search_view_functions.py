'''
Created on 4 May 2018

@author: fer
'''

from .models import Episode, Program, Tag, Station, User
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.aggregates import StringAgg

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
    


def textbox_search_episode(word_list,page=1,search_tags=False):
    
    result_qs = Episode.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
        
        if search_tags:
            vector = SearchVector('title','tag__name','summary')
        else:
            vector = SearchVector('title','summary')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank','-publication_date')

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)
        


def textbox_search_program(word_list,page=1,search_tags=False):
    
    result_qs = Program.objects.all()
    
    try:
    
        query_or = _aux_create_search_query(word_list)
        
        if search_tags:
            vector = SearchVector('name',StringAgg('tag__name', delimiter=' '),'description')
        else:
            vector = SearchVector('name','description')
            
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
        
        result_qs = qs_or.order_by('-rank').distinct()

    except IndexError:
        pass


    return _aux_paginator_creation(result_qs,page)
    


def _aux_get_size(tu,size_list):

    try:
        return next(x[0] for x in enumerate(size_list) if x[1] >= tu)
    except StopIteration:
        return len(size_list)-1



def get_tag_cloud(size,categories=10):
    
    tags = list(Tag.objects.order_by('-times_used')[0:size])
    max_value = tags[0].times_used
    min_value = tags[-1].times_used
    tags.sort(key=lambda x: x.name, reverse=False)
    ts_list = []

    if categories < 2:
       
        for tag in tags:
            ts_list.append({'name':tag.name,'size':0}) 
        
    elif len(tags)>categories:
        
        category_step = (max_value - min_value)/categories
        
        size_list = [min_value]
        for _ in range(1,categories-1):
            size_list.append(size_list[-1]+category_step)
        size_list.append(max_value+1)
        
        for tag in tags:
            ts_list.append({'name':tag.name,'size':_aux_get_size(tag.times_used,size_list)}) 
    
    else:
        
        tags.sort(key=lambda x: x.name, reverse=False)
        index = 0
        
        for tag in tags:
            
            ts_list.append({'name':tag.name,'size':index})
            index += 1
            
    return ts_list
    


