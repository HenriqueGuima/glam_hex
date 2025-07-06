from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='backoffice_login'),
    path('dashboard/', views.dashboard_view, name='backoffice_dashboard'),
    path('logout/', views.logout_view, name='backoffice_logout'),
    path('manage-user/', views.manage_user_view, name='backoffice_manage_user'),
    path('add-user/', views.add_user_view, name='backoffice_add_user'),
    path('add-picture/', views.add_picture_view, name='backoffice_add_picture'),
    path('manage-pictures/', views.manage_pictures_view, name='backoffice_manage_pictures'),
    path('upload-banner/', views.upload_banner_view, name='backoffice_upload_banner'),
    path('upload-about-picture/', views.upload_about_picture_view, name='backoffice_upload_about_picture'),
    path('calendar/', views.calendar_view, name='backoffice_calendar'),
    path('upload-social-makeup/', views.upload_social_makeup_picture_view, name='backoffice_upload_social_makeup_picture'),
    path('upload-glow/', views.upload_glow_picture_view, name='backoffice_upload_glow_picture'),
    path('upload-mature/', views.upload_mature_picture_view, name='backoffice_upload_mature_picture'),
    path('upload-natural/', views.upload_natural_picture_view, name='backoffice_upload_natural_picture'),
    path('upload-artistic/', views.upload_artistic_picture_view, name='backoffice_upload_artistic_picture'),
    path('upload-videoclip/', views.upload_videoclip_picture_view, name='backoffice_upload_videoclip_picture'),
    path('calendar-export/', views.calendar_export_ics, name='backoffice_calendar_export_ics'),
]
