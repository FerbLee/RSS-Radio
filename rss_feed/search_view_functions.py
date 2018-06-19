# RSS-Radio - Online service for publishing radio broadcasting recordings and podcasts.
# Copyright (C) 2018  Fernando Liñares Varela
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
            vector = SearchVector(StringAgg('tag__name', delimiter=' '),'title','summary')
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
            vector = SearchVector(StringAgg('tag__name', delimiter=' '),'name','description')
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
    

def get_paginated_subs(user,page=1,ps=PAGE_SIZE):
                
    subs_programs = user.subscribers.all()
    subs_episodes = Episode.objects.none()
    
    for program in subs_programs:
        
        subs_episodes = program.episode_set.all()|subs_episodes
    
    result_qs = subs_episodes.order_by('-publication_date')
    
    return _aux_paginator_creation(result_qs,page,ps)    
 

def get_paginated_pop_programs(page=1,ps=PAGE_SIZE):
    
    result_qs = Program.objects.order_by('-popularity')
    return _aux_paginator_creation(result_qs,page,ps)  
    
    
def get_paginated_latest_episodes(page=1,ps=PAGE_SIZE):   
    
    result_qs = Episode.objects.order_by('-publication_date')
    return _aux_paginator_creation(result_qs,page,ps)


def get_paginated_stations(user=None,page=1,ps=PAGE_SIZE):
    
    if user == None:
        result_qs = Station.objects.order_by('id')
    else:
        result_qs = user.followers.order_by('name')
    
    return _aux_paginator_creation(result_qs,page,ps)
    

def get_paginated_program_episodes(program,page=1,ps=PAGE_SIZE):
    
    result_qs = program.episode_set.order_by('-publication_date')
    return _aux_paginator_creation(result_qs,page,ps)


def get_paginated_program_stations(program,page=1,ps=PAGE_SIZE):
    
    bc_qs = program.broadcast_set.order_by('station__id').prefetch_related('station')
    #result_qs = [bc.station for bc in bc_qs]
    result_qs = bc_qs
    return _aux_paginator_creation(result_qs,page,ps)


def get_paginated_program_subscribers(program,page=1,ps=PAGE_SIZE):
    
    result_qs = program.subscribers.order_by('username')
    return _aux_paginator_creation(result_qs,page,ps)


def get_paginated_station_latest_episodes(station,page=1,ps=PAGE_SIZE): 
    
        subs_programs = station.programs.all()
        subs_episodes = Episode.objects.none()
        
        for program in subs_programs:
            
            subs_episodes = program.episode_set.all()|subs_episodes
        
        result_qs = subs_episodes.order_by('-publication_date')
        return _aux_paginator_creation(result_qs,page,ps)
 
 
def get_paginated_station_programs(station,page=1,ps=PAGE_SIZE): 
     
        result_qs = station.broadcast_set.order_by('program__id').prefetch_related('program')
        #result_qs = station.programs.order_by('id')
        return _aux_paginator_creation(result_qs,page,ps)
    
    
def get_paginated_station_followers(station,page=1,ps=PAGE_SIZE): 
       
        result_qs = station.followers.order_by('id')
        return _aux_paginator_creation(result_qs,page,ps)
        

def get_paginated_user_sub_programs(user,page=1,ps=PAGE_SIZE):
        
    result_qs = user.subscribers.order_by('id')
    return _aux_paginator_creation(result_qs,page,ps)


def get_paginated_user_foll_stations(user,page=1,ps=PAGE_SIZE):
    
    result_qs = user.followers.order_by('id')
    return _aux_paginator_creation(result_qs,page,ps)

    
def get_paginated_user_adm_programs(user,page=1,ps=PAGE_SIZE):
    
    result_qs = user.programs_admin.order_by('program__id')
    return _aux_paginator_creation(result_qs,page,ps)

    
def get_paginated_user_adm_stations(user,page=1,ps=PAGE_SIZE):    
        
    result_qs = user.stations_admin.order_by('station__id').prefetch_related('station')
    return _aux_paginator_creation(result_qs,page,ps)

