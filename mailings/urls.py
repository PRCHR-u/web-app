from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('register/', views.register, name='register'),
    
    # Главная страница
    path('', views.dashboard, name='dashboard'),
    
    # Клиенты
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    # Рассылки
    path('mailings/', views.mailing_list, name='mailing_list'),
    path('mailings/create/', views.mailing_create, name='mailing_create'),
    path('mailings/<int:pk>/', views.mailing_detail, name='mailing_detail'),
    path('mailings/<int:pk>/edit/', views.mailing_edit, name='mailing_edit'),
    path('mailings/<int:pk>/delete/', views.mailing_delete, name='mailing_delete'),
    path('mailings/<int:pk>/send/', views.mailing_send_now, name='mailing_send_now'),
    
    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    
    # Логи
    path('logs/', views.logs_list, name='logs_list'),
] 