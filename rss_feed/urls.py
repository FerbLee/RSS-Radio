'''
Created on 12 Sep 2017

@author: fer
'''

# Pre-generic view code

from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

app_name = 'rss_feed'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^addLink/$', views.addLink, name='addLink'),
    url(r'^program/(?P<pk>[0-9]+)/$', views.ProgramDetailView.as_view(), name='detail_program'),
    url(r'^episode/(?P<pk>[0-9]+)/$', views.EpisodeDetailView.as_view(), name='detail_episode'),
    url(r'^user/(?P<pk>[0-9]+)/$', views.UserDetailView.as_view(), name='detail_user'),
    url(r'^edit_user/$', views.user_edit,name='edit_user')] 

#urlpatterns +=  staticfiles_urlpatterns() + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)