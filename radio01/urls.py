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

"""radio01 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
import rss_feed.views as core_views
from django.contrib.auth.views import logout
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    url(r'^rss_feed/', include('rss_feed.urls')),
    url(r'^admin/', admin.site.urls),
    url('^registration/', include('django.contrib.auth.urls')),
    url(r'^registration/signup/$', core_views.signup, name='signup'),
    url(r'^registration/logout/$', logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    
]

urlpatterns +=  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
