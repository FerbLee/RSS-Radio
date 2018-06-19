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