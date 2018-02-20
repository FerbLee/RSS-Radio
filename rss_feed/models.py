from django.db import models
from django.utils import timezone
import datetime

ML_DESCRIPTION = 1000
ML_NAME = 200
ML_AUTHOR = 200 
ML_TITLE = 200
ML_LINKS = 500
ML_TYPE = 20

# Create your models here.
class Program(models.Model):
       
    name = models.CharField(max_length=ML_NAME)
    author = models.CharField(max_length=ML_AUTHOR ,null=True)
    description = models.CharField(max_length=ML_DESCRIPTION)
    creation_date = models.DateTimeField('date created')
    rss_link = models.CharField(max_length=500)

    def __str__(self):
        return self.name

    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)



class Episode(models.Model):
    
    def __str__(self):
        return self.title
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    title = models.CharField(max_length=ML_TITLE)
    publication_date = models.DateTimeField('date published')
    summary = models.CharField(max_length=ML_DESCRIPTION)
    file = models.CharField(max_length=ML_LINKS)
    file_type = models.CharField(max_length=ML_TYPE)
