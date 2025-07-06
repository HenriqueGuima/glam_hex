from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=50, default='user')

class Picture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class BannerPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class AboutPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

class SiteVisit(models.Model):
    date = models.DateField(unique=True)
    count = models.IntegerField(default=0)

    class Meta:
        db_table = 'site_visits'

class SocialMakeupPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class GlowPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class MaturePicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class NaturalPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class ArtisticPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)

class VideoclipPicture(models.Model):
    url = models.CharField(max_length=255)
    uploaded = models.DateTimeField(auto_now_add=True)