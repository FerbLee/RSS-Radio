from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
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

IMAGE_DIR_PATH = '/home/fer/eclipse-workspace/RSS-Radio/rss_feed/images'

# Create your models here.

class Image(models.Model):
    
    def __str__(self):
        return self.title
    
    path = models.ImageField(default=os.path.join(IMAGE_DIR_PATH,'default.jpg'))
    name = models.CharField(max_length=ML_NAME,null=True)
    alt_text = models.CharField(max_length=ML_NAME,default='Image')



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
    
    def __str__(self):
        return self.title
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    title = models.CharField(max_length=ML_TITLE)
    publication_date = models.DateTimeField(default=default_time)
    insertion_date = models.DateTimeField(default=default_time) 
    summary = models.CharField(max_length=ML_DESCRIPTION)
    file = models.URLField()
    file_type = models.CharField(max_length=ML_TYPE,null=True)
    downloads = models.BigIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(default=50,validators=[MaxValueValidator(100), MinValueValidator(0)])
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)


