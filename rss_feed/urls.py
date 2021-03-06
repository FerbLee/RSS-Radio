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
Created on 12 Sep 2017

@author: fer
'''

# Pre-generic view code

from django.conf.urls import url
from django.views.defaults import page_not_found
from . import views

app_name = 'rss_feed'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    #url(r'^addLink/$', views.addLink, name='addLink'),
    url(r'^program/(?P<pk>[0-9]+)/$', views.ProgramDetailView.as_view(), name='detail_program'),
    url(r'^episode/(?P<pk>[0-9]+)/$', views.EpisodeDetailView.as_view(), name='detail_episode'),
    url(r'^user/(?P<pk>[0-9]+)/$', views.UserDetailView.as_view(), name='detail_user'),
    url(r'^edit_user/$', views.user_edit,name='edit_user'),
    url(r'^edit_station/(?P<pk>[0-9]+)/$', views.station_edit,name='edit_station'),
    url(r'^edit_program/(?P<pk>[0-9]+)/$', views.program_edit,name='edit_program'),
    url(r'^manage_station/(?P<pk>[0-9]+)/$', views.ManageStationView.as_view(),name='manage_station'),
    url(r'^manage_program/(?P<pk>[0-9]+)/$', views.ManageProgramView.as_view(),name='manage_program'),
    url(r'^admin_station/(?P<pk>[0-9]+)/$', views.AdminStationView.as_view(),name='admin_station'),
    url(r'^admin_program/(?P<pk>[0-9]+)/$', views.AdminProgramView.as_view(),name='admin_program'),
    url(r'^add_broadcast/(?P<pk>[0-9]+)/$', views.add_broadcast,name='add_broadcast'),
    url(r'^delete_broadcast2(?P<pk>[0-9]+)/', views.delete_broadcast,name='delete_broadcast'),
    url(r'^program_delete_broadcast(?P<pk>[0-9]+)/', views.program_delete_broadcast,name='program_delete_broadcast'),
    url(r'^add_admin/(?P<pk>[0-9]+)/(?P<type>[\w-]+)$', views.add_admin,name='add_admin'),
    url(r'^edit_admin/(?P<pk>[0-9]+)/(?P<type>[\w-]+)/', views.edit_admin,name='edit_admin'),
    url(r'^delete_station/(?P<pk>[0-9]+)/$', views.delete_station, name='delete_station'),
    url(r'^delete_program/(?P<pk>[0-9]+)/$', views.delete_program, name='delete_program'),
    url(r'^predelete_station/(?P<pk>[0-9]+)/$', views.DeleteStationPreview.as_view(), name='predelete_station'),
    url(r'^predelete_program/(?P<pk>[0-9]+)/$', views.DeleteProgramPreview.as_view(), name='predelete_program'),
    url(r'^add_content/$', views.add_content,name='add_content'),
    url(r'^station/(?P<pk>[0-9]+)/$', views.StationDetailView.as_view(),name='detail_station'),
    url(r'^follow-station/(?P<pk>[0-9]+)/$', views.follow_station, name='follow_station'),
    url(r'^unfollow-station/(?P<pk>[0-9]+)/$', views.unfollow_station, name='unfollow_station'),
    url(r'^subscribe-program/(?P<pk>[0-9]+)/$', views.subscribe_program, name='subscribe_program'),
    url(r'^unsubscribe-program/(?P<pk>[0-9]+)/$', views.unsubscribe_program, name='unsubscribe_program'),
    url(r'^vote-episode/(?P<pk>[0-9]+)/(?P<type>[\w-]+)$', views.vote_episode, name='vote_episode'),
    url(r'^delete-comment/(?P<epk>[0-9]+)/(?P<cpk>[0-9]+)/$', views.delete_comment, name='delete_comment'),
    url(r'^deleted/', views.deleted_content, name='deleted'),
    url(r'^error/', views.error, name='error'),
    url(r'^search_results/$', views.search,name='search_results'),
    url(r'^download/$', views.download,name='download'),
    #url(r'^search/$', views.search,name='search'),
    url(r'^unknown/$', page_not_found,  kwargs={'exception': Exception('Page not Found')},name='unknown'),]

#urlpatterns +=  staticfiles_urlpatterns() + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


