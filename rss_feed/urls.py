'''
Created on 12 Sep 2017

@author: fer
'''

# Pre-generic view code

from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
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
    url(r'^add_content/$', views.add_content,name='add_content'),
    url(r'^station/(?P<pk>[0-9]+)/$', views.StationDetailView.as_view(),name='detail_station'),
    url('^follow-station/(?P<pk>[0-9]+)/$', views.follow_station, name='follow_station'),
    url('^unfollow-station/(?P<pk>[0-9]+)/$', views.unfollow_station, name='unfollow_station'),
    url('^subscribe-program/(?P<pk>[0-9]+)/$', views.subscribe_program, name='subscribe_program'),
    url('^unsubscribe-program/(?P<pk>[0-9]+)/$', views.unsubscribe_program, name='unsubscribe_program'),
    url('^vote-episode/(?P<pk>[0-9]+)/(?P<type>[\w-]+)$', views.vote_episode, name='vote_episode'),
    url(r'^unknown/$', page_not_found,  kwargs={'exception': Exception('Page not Found')},name='unknown'),]

#urlpatterns +=  staticfiles_urlpatterns() + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


