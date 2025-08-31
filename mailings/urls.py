from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Аутентификация
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='login'),
        name='logout'
    ),
    path('register/', views.register, name='register'),
    path(
        'activate/<uidb64>/<token>/',
        views.activate,
        name='activate'
    ),

    # Главная страница
    path('', views.dashboard, name='dashboard'),

    # Клиенты
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path(
        'clients/<int:pk>/delete/',
        views.client_delete,
        name='client_delete'
    ),

    # Рассылки
    path('mailings/', views.mailing_list, name='mailing_list'),
    path('mailings/create/', views.mailing_create, name='mailing_create'),
    path('mailings/<int:pk>/', views.mailing_detail, name='mailing_detail'),
    path('mailings/<int:pk>/edit/', views.mailing_edit, name='mailing_edit'),
    path(
        'mailings/<int:pk>/delete/',
        views.mailing_delete,
        name='mailing_delete'
    ),
    path(
        'mailings/<int:pk>/disable/',
        views.mailing_disable,
        name='mailing_disable'
    ),
    path(
        'mailings/<int:pk>/send/',
        views.send_mailing,
        name='send_mailing'
    ),
    path('reports/', views.user_mailing_reports, name='user_mailing_reports'),
    path('mailing-logs/', views.mailing_log_list, name='mailing_log_list'),
    path('logs/', views.mailing_log_list, name='logs_list'),


    # Шаблоны сообщений
    path('message-templates/', views.message_template_list, name='message_template_list'),
    path(
        'message-templates/create/',
        views.message_create,
        name='message_template_create'
    ),
    path(
        'message-templates/<int:pk>/',
        views.message_detail,
        name='message_template_detail'
    ),
    path(
        'message-templates/<int:pk>/edit/',
        views.message_edit,
        name='message_template_edit'
    ),
    path(
        'message-templates/<int:pk>/delete/',
        views.message_delete,
        name='message_template_delete'
    ),

    # Сообщения
    path('messages/', views.sent_message_list, name='sent_message_list'),

    # Сброс пароля
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
]
