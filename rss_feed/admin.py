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
from django.contrib import admin
from .models import Program, Episode, Station, Comment, Vote, Broadcast, Tag
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Register your models here.

admin.site.register(Program)
admin.site.register(Episode)
admin.site.register(Station)
admin.site.register(Comment)
admin.site.register(Vote)
admin.site.register(Broadcast)
admin.site.register(Tag)

# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
admin.site.unregister(User)
admin.site.register(User, UserAdmin)