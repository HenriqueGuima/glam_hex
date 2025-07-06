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
]
