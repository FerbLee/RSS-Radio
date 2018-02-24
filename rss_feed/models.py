from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings
import os
from datetime import datetime
import pytz

default_time = datetime(1,1,1,0,0,0,0,tzinfo=pytz.UTC)

#ML_DESCRIPTION = 300
ML_NAME = 200
ML_AUTHOR = 200 
ML_TITLE = 200
#ML_LINKS = 500
ML_TYPE = 40
ML_ORIGINAL_ID = 200
ML_TAG = 50

EXISTING_CATEGORIES = (('re','revista'),('hu','humor'),('in','informativo'),('te','tertulia'),('en','entretemento'),
                       ('di','divulgativo'),('ou','outros'))

IVOOX_TYPE = ('iv','ivoox')
RADIOCO_TYPE = ('ra','radioco')
PODOMATIC_TYPE = ('po','podomatic')

EXISTING_PARSERS = (IVOOX_TYPE,RADIOCO_TYPE,PODOMATIC_TYPE)

DEFAULT_IMAGES_DIR = 'default'
ABSOLUTE_DEFAULT_IMAGES_DIR = os.path.join(settings.MEDIA_ROOT,DEFAULT_IMAGES_DIR) 
DEFAULT_IMAGE_PATH = os.path.join(DEFAULT_IMAGES_DIR,'program.jpg')
#ABSOLUTE_DEFAULT_IMAGE_PATH = os.path.join(ABSOLUTE_DEFAULT_IMAGES_DIR,'program.jpg')
IMAGE_DIR = 'pictures'
ABSOLUTE_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT,IMAGE_DIR)

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
        
    #@classmethod
    #def default_images_creation(cls):
    #    
    #    cls.default_program_image_creation()
        
        

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

    def __str__(self):
        return self.name

    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)



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

    def __str__(self):
        return self.title


class Tag(models.Model):

    name = TruncatingCharField(max_length=ML_TAG)
    times_used = models.PositiveIntegerField(default=1)
    programs = models.ManyToManyField(Program)
    episodes = models.ManyToManyField(Episode)
    
    def __str__(self):
        
        return str(self.name)
    
    
