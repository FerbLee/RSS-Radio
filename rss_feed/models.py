from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings
import os
from datetime import datetime
import pytz
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from django.db.models.signals import post_save

default_time = datetime(1975,1,1,0,0,0,0,tzinfo=pytz.UTC)

ML_DESCRIPTION = 300
ML_NAME = 200
ML_AUTHOR = 200 
ML_TITLE = 200
#ML_LINKS = 500
ML_TYPE = 40
ML_ORIGINAL_ID = 200
ML_TAG = 50

EXISTING_CATEGORIES = (('re','revista'),('hu','humor'),('in','informativo'),('te','tertulia'),('en','entretemento'),
                       ('di','divulgativo'),('ou','outros'))

EXISTING_BCMETHODS = (('fm','Radio FM/AM'),('in','Radio Internet'),('di','Radio Digital'),
                      ('pc','Podcasting Channel'),('tv','TV Channel'),('ot','Others'))

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
    # Author (RSS link) ! = Owner (System user)
    author = TruncatingCharField(max_length=ML_AUTHOR ,null=True)
    author_email = models.EmailField(null=True)
    language = TruncatingCharField(max_length=10,null=True)
    description = models.TextField()
    creation_date = models.DateTimeField(default=default_time)
    rss_link = models.URLField()
    rss_link_type = models.CharField(choices=EXISTING_PARSERS,max_length=2,default='ra')
    rating = models.PositiveSmallIntegerField(default=50,validators=[MaxValueValidator(100), MinValueValidator(0)])
    category = models.CharField(choices=EXISTING_CATEGORIES,max_length=2,default='ou')
    original_site = models.URLField(null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    removed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


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
    up_votes = models.BigIntegerField(default=0)
    down_votes = models.BigIntegerField(default=0)
    original_id = TruncatingCharField(max_length=ML_ORIGINAL_ID,null=True)
    original_site = models.URLField(null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    removed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Tag(models.Model):

    name = TruncatingCharField(max_length=ML_TAG)
    times_used = models.PositiveIntegerField(default=1)
    programs = models.ManyToManyField(Program)
    episodes = models.ManyToManyField(Episode)
    
    def __str__(self):
        
        return str(self.name)
    
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
    programs = models.ManyToManyField(Program,through='Emission')
    admins = models.ManyToManyField(User,related_name='admins')
    followers = models.ManyToManyField(User,related_name='followers')
    
    def __str__(self):
        
        return str(self.name)
    
    
class Emission(models.Model):
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    station =  models.ForeignKey(Station, on_delete=models.CASCADE)
    emission_time = TruncatingCharField(max_length=100,null=True)
    periodicity = TruncatingCharField(max_length=100,null=True)
    
        
