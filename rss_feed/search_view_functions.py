'''
Created on 4 May 2018

@author: fer
'''

from .models import Episode, Program, Image, Station
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank


def textbox_search_episode(word_list):
    
    result_qs = Episode.objects.all()
    
    if word_list != []:
        
        query_or = SearchQuery(word_list[0])  
            
        for word in word_list[1:]:
            query_or = query_or |  SearchQuery(word) 
        
        
        vector = SearchVector('title', 'summary')
        
        qs_or = result_qs.annotate(search=vector).filter(search=query_or)
        qs_or = qs_or.annotate(rank=SearchRank(vector, query_or))
        
        result_qs = qs_or.order_by('-rank','-publication_date')

    return result_qs
        
        
