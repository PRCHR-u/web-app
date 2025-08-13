from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'), # Added URL pattern for profile view
    path('profile/edit/', views.edit_profile, name='edit_profile'), # Added URL pattern for edit profile view
]
