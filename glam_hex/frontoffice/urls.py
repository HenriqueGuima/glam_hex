from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='frontoffice_home'),
    path('about/', views.about_view, name='frontoffice_about'),
]
