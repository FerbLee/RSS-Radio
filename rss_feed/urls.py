'''
Created on 12 Sep 2017

@author: fer
'''

# Pre-generic view code

from django.conf.urls import url

from . import views

app_name = 'rss_feed'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^addLink/$', views.addLink, name='addLink'),
    url(r'^programa/(?P<pk>[0-9]+)/$', views.ProgramaDetailView.as_view(), name='detail_programa'),
    url(r'^episodio/(?P<pk>[0-9]+)/$', views.EpisodioDetailView.as_view(), name='detail_episodio')
    #url(r'^(?P<pk>[0-9]+)/programs/$', views.ResultsView.as_view(), name='programs'),
    #url(r'^(?P<programa_id>[0-9]+)/episodes/$', views.vote, name='episode'),
]