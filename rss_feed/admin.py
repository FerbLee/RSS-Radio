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