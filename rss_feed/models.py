from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings
import os
from datetime import datetime
import pytz

default_time = datetime(1,1,1,0,0,0,0,tzinfo=pytz.UTC)

ML_DESCRIPTION = 1000
ML_NAME = 200
ML_AUTHOR = 200 
ML_TITLE = 200
#ML_LINKS = 500
ML_TYPE = 40

EXISTING_CATEGORIES = (('re','revista'),('hu','humor'),('in','informativo'),('te','tertulia'),('en','entretemento'),
                       ('di','divulgativo'),('ou','outros'))


DEFAULT_IMAGES_DIR = 'default'
ABSOLUTE_DEFAULT_IMAGES_DIR = os.path.join(settings.MEDIA_ROOT,DEFAULT_IMAGES_DIR) 
DEFAULT_IMAGE_PATH = os.path.join(DEFAULT_IMAGES_DIR,'program.jpg')
IMAGE_DIR = 'pictures'
ABSOLUTE_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT,IMAGE_DIR)

# Create your models here.

class Image(models.Model):
    
    path = models.ImageField(upload_to=IMAGE_DIR+'/%Y/%m/',default=DEFAULT_IMAGE_PATH)
    original_url = models.URLField(null=True)
    creation_date = models.DateTimeField(default=default_time,null=True)
    name = models.CharField(max_length=ML_NAME,null=True)
    alt_text = models.CharField(max_length=ML_NAME,default='Image')

    
    def __str__(self):
        
        return str(self.path)
    
    
    @classmethod
    def default_program_image_creation(cls):
            
        new_program_def_img = Image()
        new_program_def_img.creation_date = timezone.now()
        new_program_def_img.path = ABSOLUTE_DEFAULT_IMAGES_DIR 
        new_program_def_img.name = 'Program-Episode default image'
        new_program_def_img.alt_text = 'default-image'
        
        new_program_def_img.save()
        
        return new_program_def_img
    
    
    @classmethod
    def get_default_program_image(cls):
        
        program_def_img = cls.objects.filter(path=DEFAULT_IMAGE_PATH)
        
        if not program_def_img:
    
            return cls.default_program_image_creation()
        
        return program_def_img[-1]
        
    #@classmethod
    #def default_images_creation(cls):
    #    
    #    cls.default_program_image_creation()
        
        


class Program(models.Model):
       
    name = models.CharField(max_length=ML_NAME)
    author = models.CharField(max_length=ML_AUTHOR ,null=True)
    description = models.CharField(max_length=ML_DESCRIPTION)
    creation_date = models.DateTimeField(default=default_time)
    rss_link = models.URLField()
    rating = models.PositiveSmallIntegerField(default=50,validators=[MaxValueValidator(100), MinValueValidator(0)])
    category = models.CharField(choices=EXISTING_CATEGORIES,max_length=2,default='ou')
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)



class Episode(models.Model):
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    title = models.CharField(max_length=ML_TITLE)
    publication_date = models.DateTimeField(default=default_time)
    insertion_date = models.DateTimeField(default=default_time) 
    summary = models.CharField(max_length=ML_DESCRIPTION)
    file = models.URLField()
    file_type = models.CharField(max_length=ML_TYPE,null=True)
    downloads = models.BigIntegerField(default=0)
    up_votes = models.BigIntegerField(default=0)
    down_votes = models.BigIntegerField(default=0)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title


