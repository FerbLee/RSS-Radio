from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
import os
from datetime import datetime
import pytz
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

default_time = datetime(1975,1,1,0,0,0,0,tzinfo=pytz.UTC)

ML_DESCRIPTION = 300
ML_NAME = 200
ML_AUTHOR = 200 
ML_TITLE = 200
#ML_LINKS = 500
ML_TYPE = 40
ML_ORIGINAL_ID = 200
ML_TAG = 50

CO_ENABLE = ('en',_('Enable'))
CO_DISABLE = ('di',_('Disable'))
EXISTING_COMMENT_OPTIONS = (CO_ENABLE,CO_DISABLE)

SH_TF = ('tf',_('share free'))
SH_AF = ('af',_('ask first'))
SH_NS = ('ns',_('no share'))
SHAREABLE_OPTIONS = [SH_TF]
EXISTING_SHARING_OPTS = (SH_TF,SH_NS )

LIKE_VOTE = ('lk',_('like'))
DISLIKE_VOTE = ('dl',_('dislike'))
NEUTRAL_VOTE = ('ne',_('neutral'))
EXISTING_VOTE_TYPES = (LIKE_VOTE,DISLIKE_VOTE,NEUTRAL_VOTE)

BCM_FM = ('fm',_('Radio FM/AM'))
BCM_DIGITAL = ('di',_('Radio Digital'))
BCM_TV = ('tv',_('TV Channel'))
EXISTING_BCMETHODS = (BCM_FM, BCM_DIGITAL, BCM_TV, ('in',_('Radio Internet')),
                      ('pc',_('Podcasting Channel')),('ot',_('Others')))

ADMT_OWNER = ('ow',_('Owner'))
ADMT_ADMIN = ('ad',_('Admin'))
EXISTING_ADMIN_TYPES = (ADMT_OWNER,ADMT_ADMIN)


IVOOX_TYPE = ('iv','ivoox')
RADIOCO_TYPE = ('ra','radioco')
PODOMATIC_TYPE = ('po','podomatic')

EXISTING_PARSERS = (IVOOX_TYPE,RADIOCO_TYPE,PODOMATIC_TYPE)

DEFAULT_IMAGES_DIR = 'default'
ABSOLUTE_DEFAULT_IMAGES_DIR = os.path.join(settings.MEDIA_ROOT,DEFAULT_IMAGES_DIR) 
DEFAULT_IMAGE_PATH = os.path.join(DEFAULT_IMAGES_DIR,'program.jpg')
DEFAULT_AVATAR_PATH = os.path.join(DEFAULT_IMAGES_DIR,'avatar.png')
IMAGE_DIR = 'pictures'
ABSOLUTE_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT,IMAGE_DIR)

DEFAULT_USER_GROUP = 'RSSF-RegularUser'

# Create custom fields

class TruncatingCharField(models.CharField):
    
    def get_prep_value(self, value):
        value = super(TruncatingCharField,self).get_prep_value(value)
        if value:
            if len(value) > self.max_length:
                return value[:self.max_length-3] + '...' 
        return value


# Create your models here.    

class Image(models.Model):
    
    path = models.ImageField(upload_to=IMAGE_DIR+'/%Y/%m/',default=DEFAULT_IMAGE_PATH)
    original_url = models.URLField(null=True)
    creation_date = models.DateTimeField(default=default_time,null=True)
    name = TruncatingCharField(max_length=ML_NAME,null=True)
    alt_text = TruncatingCharField(max_length=ML_NAME,default='Image')
    
    
    def __str__(self):
        
        return str(self.path)
    
    
    def delete(self):
        
        if not DEFAULT_IMAGES_DIR in self.path.path:
            try:
                os.remove(self.path.path)
            except FileNotFoundError:
                print('Image ' + self.path.path + ' not found for deletion. Removing DB entry anyway.')
                
        super(Image, self).delete() 
    
    
    @classmethod
    def default_program_image_creation(cls):
            
        new_program_def_img = Image()
        new_program_def_img.creation_date = timezone.now()
        new_program_def_img.name = 'Program-Episode default image'
        new_program_def_img.alt_text = 'default-image'
        
        new_program_def_img.save()
        
        return new_program_def_img
    
    
    @classmethod
    def get_default_program_image(cls):
        
        program_def_img = cls.objects.filter(path=DEFAULT_IMAGE_PATH).order_by('-creation_date')
        
        if not program_def_img:
    
            return cls.default_program_image_creation()
        
        return program_def_img[0]
        
        
    @classmethod
    def default_avatar_creation(cls):
            
        default_avatar_img = Image()
        default_avatar_img.creation_date = timezone.now()
        default_avatar_img.name = 'User Avatar default image'
        default_avatar_img.alt_text = 'default-avatar'
        default_avatar_img.path = DEFAULT_AVATAR_PATH
        
        default_avatar_img.save()
        
        return default_avatar_img
    
    
    @classmethod
    def get_default_avatar(cls):
        
        program_def_img = cls.objects.filter(path=DEFAULT_AVATAR_PATH).order_by('-creation_date')
        
        if not program_def_img:
    
            return cls.default_avatar_creation()
        
        return program_def_img[0]
      
    

# Extends Django user class
class UserProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = TruncatingCharField(max_length=ML_DESCRIPTION,null=True)
    location = TruncatingCharField(max_length=100,null=True)
    avatar = models.ForeignKey(Image, on_delete=models.SET_NULL, blank=True, null=True)


    def delete(self):
        
        if not DEFAULT_IMAGES_DIR in self.avatar.path.path:
            self.avatar.delete()
            
        return super(UserProfile, self).delete()



@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    
    if created:
        
        # Add to default user group
        qs_def_group = Group.objects.filter(name=DEFAULT_USER_GROUP)
        if qs_def_group:
            qs_def_group[0].user_set.add(instance)
        
        UserProfile.objects.create(user=instance)
    
    instance.userprofile.save()



PROGRAM_ATB_FROM_RSS = ['name','author','description','original_site','author_email','language'] 

class Program(models.Model):
       
    name = TruncatingCharField(max_length=ML_NAME)
    author = TruncatingCharField(max_length=ML_AUTHOR ,null=True)
    author_email = models.EmailField(null=True)
    language = TruncatingCharField(max_length=10,null=True)
    description = models.TextField()
    creation_date = models.DateTimeField(default=default_time)
    rss_link = models.URLField()
    rss_link_type = models.CharField(choices=EXISTING_PARSERS,max_length=2,default='ra')
    rating = models.PositiveSmallIntegerField(default=50,validators=[MaxValueValidator(100), MinValueValidator(0)])
    original_site = models.URLField(null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    popularity = models.FloatField(default=0)
    website = models.URLField(default=None,null=True)
    comment_options = models.CharField(choices=EXISTING_COMMENT_OPTIONS ,max_length=2,default=CO_ENABLE[0])
    sharing_options = models.CharField(choices=EXISTING_SHARING_OPTS,max_length=2,default=SH_TF[0])
    subscribers = models.ManyToManyField(User,related_name='subscribers')
    admins = models.ManyToManyField(User,through='ProgramAdmin',related_name='program_admins')
    

    def __str__(self):
        return self.name


    def check_user_is_admin(self,user,adm_type=None):
    
        if adm_type == None:
            return self.programadmin_set.filter(user_id=user.id)
        else:
            return self.programadmin_set.filter(user_id=user.id,type=adm_type)
    
    
    def delete(self):
        
        if not DEFAULT_IMAGES_DIR in self.image.path.path:
            self.image.delete()
        
        for tag in self.tag_set.all():
            tag.decrease_times_used()
            
        return super(Program, self).delete()
    
    
    @classmethod
    def class_str_id(cls):
        
        return 'pr' 
        
    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)



class ProgramAdmin(models.Model):
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    user =  models.ForeignKey(User, on_delete=models.CASCADE,related_name='programs_admin')
    type = models.CharField(choices=EXISTING_ADMIN_TYPES,max_length=2)
    date =  models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return 'Program:' + str(self.program) + '-User:' + str(self.user) + '-' + str(self.type)



EPISODE_ATB_FROM_RSS = ['title','publication_date','summary','file','file_type','original_site']

class Episode(models.Model):
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    title = TruncatingCharField(max_length=ML_TITLE)
    publication_date = models.DateTimeField(default=default_time)
    insertion_date = models.DateTimeField(default=default_time) 
    summary = models.TextField()
    file = models.URLField()
    file_type = TruncatingCharField(max_length=ML_TYPE,null=True)
    downloads = models.BigIntegerField(default=0)
    original_id = TruncatingCharField(max_length=ML_ORIGINAL_ID,null=True)
    original_site = models.URLField(null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    removed = models.BooleanField(default=False)
    votes = models.ManyToManyField(User,through='Vote',related_name='votes')
    comments = models.ManyToManyField(User,through='Comment',related_name='comments')

    def __str__(self):
        return self.title

    
    def get_upvote_number(self):
        
        return self.vote_set.filter(type=LIKE_VOTE[0]).count()
    
    
    def get_downvote_number(self):
        
        return self.vote_set.filter(type=DISLIKE_VOTE[0]).count()


    def check_user_is_admin(self,user,adm_type=None):
        
        return self.program.check_user_is_admin(user,adm_type)
    
    
    def check_comments_enabled(self):
        
        return self.program.comment_options == CO_ENABLE[0]
    
    
    def delete(self):
                
        for tag in self.tag_set.all():
            tag.decrease_times_used()
            
        return super(Episode, self).delete()
    


class Vote(models.Model):
    
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    user =  models.ForeignKey(User, on_delete=models.CASCADE,related_name='voters')
    type = models.CharField(choices=EXISTING_VOTE_TYPES,max_length=2)
    date =  models.DateTimeField(default=default_time)


class Comment(models.Model):
    
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    user =  models.ForeignKey(User, on_delete=models.CASCADE,related_name='commenters')
    publication_date = models.DateTimeField(auto_now_add=True) 
    text = models.TextField()
    removed = models.BooleanField(default=False)


class Tag(models.Model):

    name = TruncatingCharField(max_length=ML_TAG)
    times_used = models.PositiveIntegerField(default=1)
    programs = models.ManyToManyField(Program)
    episodes = models.ManyToManyField(Episode)
    
    def __str__(self):
        
        return str(self.name)
    
    
    def decrease_times_used(self,quantity=1):
        
        new_tu = self.times_used - quantity
        
        if new_tu < 0:
            self.times_used = 0
        else:
            self.times_used = new_tu
        
        self.save()
        
        
    @classmethod
    def clean_name(cls,name):
    
        return name.lower().strip()
    

class Station(models.Model):

    name = TruncatingCharField(max_length=ML_NAME)
    description = models.TextField(blank=True)
    broadcasting_method = models.CharField(choices=EXISTING_BCMETHODS,max_length=2,default='fm')
    broadcasting_area = TruncatingCharField(max_length=200,null=True)
    broadcasting_frequency = TruncatingCharField(max_length=50,null=True)
    streaming_link = models.URLField()
    profile_img = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True,related_name='profile_img')
    logo = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True,related_name='logo')
    website = models.URLField(default=None,null=True)
    location = TruncatingCharField(max_length=200,null=True)
    programs = models.ManyToManyField(Program,through='Broadcast')
    admins = models.ManyToManyField(User,through='StationAdmin',related_name='station_admins')
    followers = models.ManyToManyField(User,related_name='followers')
    
    def __str__(self):
        
        return str(self.name)
    
    
    def check_user_is_admin(self,user,adm_type=None):
    
        if adm_type == None:
            return user.stations_admin.filter(station_id=self.id)
        else:
            return user.stations_admin.filter(station_id=self.id,type=adm_type)
    
    
    def delete(self):
        
        if not DEFAULT_IMAGES_DIR in self.logo.path.path:
            self.logo.delete()
        
        if not DEFAULT_IMAGES_DIR in self.profile_img.path.path:
            self.profile_img.delete()
            
        return super(Station, self).delete()
    
    
    @classmethod
    def class_str_id(cls):
        
        return 'st'
    
    
class Broadcast(models.Model):
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    station =  models.ForeignKey(Station, on_delete=models.CASCADE)
    schedule_details = TruncatingCharField(max_length=100,null=True)

    def __str_(self):
        
        return 'Program:' + str(self.program) + "-Station:" + str(self.station)


class StationAdmin(models.Model):
    
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    user =  models.ForeignKey(User, on_delete=models.CASCADE,related_name='stations_admin')
    type = models.CharField(choices=EXISTING_ADMIN_TYPES,max_length=2)
    date =  models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Station:' + str(self.station) + '-User:' + str(self.user) + '-' + str(self.type)
   
   
