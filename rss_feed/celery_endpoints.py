'''
Created on 28 Feb 2018

@author: fer
'''

from __future__ import absolute_import, unicode_literals
from celery import shared_task

# Create your tasks here

@shared_task
def add(x, y):
    
    return x + y

@shared_task
def update_rss_info_daemon():
    
    from rss_feed.update_rss_daemon import ud_iterate_program_table
    
    ud_iterate_program_table()


@shared_task
def update_popularity_rating_daemon():
    
    from rss_feed.update_popularity_daemon import update_pop_rating_all_programs
    
    update_pop_rating_all_programs()    