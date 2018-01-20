from django.db import models
from django.utils import timezone
import datetime

ML_DESCRICION = 1000
ML_NOME = 200
ML_AUTOR = 200 
ML_TITULO = 200
ML_LINKS = 500

# Create your models here.
class Programa(models.Model):
       
    nome = models.CharField(max_length=ML_NOME)
    autor = models.CharField(max_length=ML_AUTOR ,null=True)
    descricion = models.CharField(max_length=ML_DESCRICION)
    rss_link = models.CharField(max_length=500)

    def __str__(self):
        return self.nome

    
    #def was_published_recently(self):
    #    return self.pub_date >= timezone.now() - datetime.timedelta(days=1)



class Episodio(models.Model):
    
    def __str__(self):
        return self.titulo
    
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=ML_TITULO)
    #data_publicacion = models.DateTimeField('data publicacion')
    resumo = models.CharField(max_length=ML_DESCRICION)
    ficheiro = models.CharField(max_length=ML_LINKS)
    
