from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('confirm-email/<uidb64>/<token>/', views.confirm_email, name='confirm_email'),
    
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
    
    # Шаблоны сообщений
    path('message_templates/', views.message_template_list, name='message_template_list'),
    path('message_templates/create/', views.message_template_create, name='message_template_create'),
    path('message_templates/<int:pk>/', views.message_template_detail, name='message_template_detail'),
    path('message_templates/<int:pk>/edit/', views.message_template_edit, name='message_template_edit'),
    path('message_templates/<int:pk>/delete/', views.message_template_delete, name='message_template_delete'),
    
    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    
    # Логи
    path('logs/', views.logs_list, name='logs_list'),

    # Сброс пароля
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
] 