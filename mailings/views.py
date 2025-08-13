import uuid
from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import cache_page 
from .models import Client, Mailing, Message, MailingLog, User # Assuming User is imported or available
from .forms import ClientForm, MailingForm, UserRegistrationForm, MailingFilterForm
from .tasks import send_mailing_task


def register(request):
    """Регистрация пользователей"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Пожалуйста, подтвердите ваш email.')
            # Send confirmation email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = str(uuid.uuid4()) # Using a simple UUID for token
            user.email_verification_token = token
            user.save()
            
            mail_subject = 'Подтверждение email для сервиса рассылок'
            message = render_to_string('mailings/acc_active_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': uid,
                'token': token,
            })
            
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Ошибка в поле {field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'mailings/register.html', {'form': form})


@cache_page(60 * 15)  # Cache for 15 minutes
@login_required
def dashboard(request):
    """Главная страница с дашбордом"""
    # Статистика
    total_mailings = Mailing.objects.filter(created_by=request.user).count()
    unique_recipients_count = Client.objects.filter(mailing__created_by=request.user).distinct().count()
    # Assuming 'active' status is the correct one for 'Запущена' based on your model
    active_mailings = Mailing.objects.filter(created_by=request.user, status='active', end_time__gte=timezone.now()).count()
    # Assuming 'Создана' status is the correct one for not yet started mailings. Corrected variable name.
    created_mailings = Mailing.objects.filter(created_by=request.user, status='draft', start_time__gt=timezone.now()).count()
    # Recalculating unique recipients for clarity, though the line above is sufficient
    unique_recipients_count = Client.objects.filter(mailing__created_by=request.user).distinct().count()

    # Message statistics for the current user's mailings
    total_sent_messages = Message.objects.filter(mailing__created_by=request.user).count()
    successful_attempts = Message.objects.filter(mailing__created_by=request.user, status='sent').count()
    failed_attempts = Message.objects.filter(mailing__created_by=request.user, status='failed').count()

 # Последние рассылки
    recent_mailings = Mailing.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    
    # Последние сообщения
    recent_messages = Message.objects.filter(mailing__created_by=request.user).select_related('mailing', 'client').order_by('-created_at')[:10]
    
    context = {
        'total_mailings': total_mailings,
        'unique_recipients_count': unique_recipients_count,
        'active_mailings': active_mailings,
        'created_mailings': created_mailings,
        'total_sent_messages': total_sent_messages,
 'successful_attempts': successful_attempts,
        'total_messages': total_messages,
        'recent_mailings': recent_mailings,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'mailings/dashboard.html', context)


@login_required
def client_list(request):
    """Список клиентов"""
    if request.user.is_staff: # Managers can see all clients
        clients = Client.objects.all().order_by('-created_at')
    else: # Regular users only see their clients
        clients = Client.objects.filter(mailing__created_by=request.user).distinct().order_by('-created_at')
 # Note: This assumes clients are linked to mailings. If clients exist independently, you might need a different approach for users to see their own.

    # Поиск
    search = request.GET.get('search')
    if search:
        clients = clients.filter(
            Q(full_name__icontains=search) | 
            Q(email__icontains=search) | 
            Q(phone__icontains=search)
        )
    
    # Пагинация
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'mailings/client_list.html', {
        'page_obj': page_obj,
        'search': search
    })


@login_required
def client_create(request):
    """Создание клиента"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
 # For now, assuming a client created here isn't directly linked to a user yet. This might need adjustment based on your client-user relationship design.
            form.save()
            messages.success(request, 'Клиент успешно создан!')
            return redirect('client_list')
    else:
        form = ClientForm()
    
    return render(request, 'mailings/client_form.html', {'form': form, 'title': 'Создать клиента'})


@login_required
def client_edit(request, pk):
    """Редактирование клиента"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования этого клиента.")
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент успешно обновлен!')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'mailings/client_form.html', {
        'form': form, 
        'title': 'Редактировать клиента',
        'client': client
    })


@login_required
def client_delete(request, pk):
    """Удаление клиента"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления этого клиента.")
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Клиент успешно удален!')
        return redirect('client_list')
    
    return render(request, 'mailings/client_confirm_delete.html', {'client': client})


@login_required
def mailing_list(request):
    """Список рассылок"""
    if request.user.is_staff: # Managers see all mailings
        mailings = Mailing.objects.all().order_by('-created_at')
    else: # Regular users see only their mailings
        mailings = Mailing.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Фильтрация и поиск
    filter_form = MailingFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['status']:
            mailings = mailings.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['frequency']:
            mailings = mailings.filter(frequency=filter_form.cleaned_data['frequency'])
        if filter_form.cleaned_data['search']:
            mailings = mailings.filter(
                Q(title__icontains=filter_form.cleaned_data['search']) |
                Q(subject__icontains=filter_form.cleaned_data['search'])
            )
    
    # Пагинация
    paginator = Paginator(mailings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'mailings/mailing_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form
    })

@login_required
def message_create(request):
    """Создание шаблона сообщения"""
    if request.method == 'POST':
        form = MessageForm(request.POST) # Assuming MessageForm exists for Message model (template)
        if form.is_valid():
            message_template = form.save(commit=False)
            message_template.created_by = request.user # Assign the logged-in user as the creator
            message_template.save()
            messages.success(request, 'Шаблон сообщения успешно создан!')
            # Redirect to the message list page (assuming 'message_list' is the name for template list)
            return redirect(reverse_lazy('message_list'))
    else:
        form = MessageForm() # Assuming MessageForm exists for Message model (template)

    return render(request, 'mailings/message_form.html', {
        'form': form,
        'title': 'Создать шаблон сообщения'
    })


@login_required
def mailing_create(request):
    """Создание рассылки"""
    if request.user.is_staff:
        messages.error(request, "Менеджеры не могут создавать рассылки.")
    if request.method == 'POST':
        form = MailingForm(request.POST, user=request.user)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.created_by = request.user
            mailing.save()
            form.save_m2m()  # Сохраняем связи many-to-many
            
            messages.success(request, 'Рассылка успешно создана!')
            return redirect('mailing_list')
    else:
        form = MailingForm(user=request.user)
    
    return render(request, 'mailings/mailing_form.html', {
        'form': form, 
        'title': 'Создать рассылку'
    })


@login_required
def mailing_edit(request, pk):
    """Редактирование рассылки"""
    if request.user.is_staff:
 # Managers can view but not edit/delete others' mailings
        mailing = get_object_or_404(Mailing, pk=pk)
    else:
        mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = MailingForm(request.POST, instance=mailing, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рассылка успешно обновлена!')
            return redirect('mailing_list')
    else:
        form = MailingForm(instance=mailing, user=request.user)
    
    return render(request, 'mailings/mailing_form.html', {
        'form': form, 
        'title': 'Редактировать рассылку',
        'mailing': mailing
    })


@login_required
def mailing_delete(request, pk):
    """Удаление рассылки"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления этой рассылки.")
    mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user) # Only creator can delete
    
    if request.method == 'POST':
        mailing.delete()
        messages.success(request, 'Рассылка успешно удалена!')
        return redirect('mailing_list')
    
    return render(request, 'mailings/mailing_confirm_delete.html', {'mailing': mailing})


@login_required
def mailing_detail(request, pk):
    """Детальная информация о рассылке"""
    if request.user.is_staff:
        mailing = get_object_or_404(Mailing, pk=pk)
    else:
        mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
    messages_list = Message.objects.filter(mailing=mailing).select_related('client').order_by('-created_at')
    
    # Статистика
    total_messages = messages_list.count()
    sent_messages = messages_list.filter(status='sent').count()
    failed_messages = messages_list.filter(status='failed').count()
    pending_messages = messages_list.filter(status='pending').count()
    
    # Пагинация для сообщений
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'mailing': mailing,
        'page_obj': page_obj,
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'failed_messages': failed_messages,
        'pending_messages': pending_messages,
    }
    
    return render(request, 'mailings/mailing_detail.html', context)


@login_required
@require_POST
def send_mailing(request, pk):
    """Триггер ручной отправки рассылки. (Доступно только создателю или менеджеру)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для запуска рассылок вручную.")
        return redirect('dashboard') # Redirect if not authorized
    mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user) # Only creator or manager can trigger? This needs clarification
    send_mailing_task.delay(mailing.id)
    messages.success(request, f'Рассылка "{mailing.title}" успешно запущена вручную!')
    return redirect('mailing_detail', pk=mailing.id) # Redirect to the mailing detail page



@login_required
@require_POST
def mailing_send_now(request, pk):
    """Отправка рассылки немедленно (Доступно только создателю или менеджеру)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для немедленной отправки рассылок.")
        return redirect('dashboard') # Redirect if not authorized
    else:
        mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)

        if mailing.status == 'active':
            # Запускаем задачу отправки
            send_mailing_task.delay(mailing.id)
            messages.success(request, 'Рассылка запущена!')
        else:
            messages.error(request, 'Рассылка должна быть активной для отправки.')
        return redirect('mailing_detail', pk=pk)


@login_required
def message_list(request):
    """Список всех сообщений пользователя"""
    if request.user.is_staff:
        messages_list = Message.objects.all().select_related('mailing', 'client').order_by('-created_at')
    else:
        messages_list = Message.objects.filter(mailing__created_by=request.user).select_related('mailing', 'client').order_by('-created_at')

    # Фильтрация по статусу
    status = request.GET.get('status')
    if status:
        messages_list = messages_list.filter(status=status)
    
    # Пагинация
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'mailings/message_list.html', {
        'page_obj': page_obj,
        'status': status
    })


@login_required
def logs_list(request):
    """Список логов рассылок"""
    if request.user.is_staff:
        logs = MailingLog.objects.all().select_related('mailing').order_by('-created_at')
    else:
        logs = MailingLog.objects.filter(mailing__created_by=request.user).select_related('mailing').order_by('-created_at')

    # Фильтрация по уровню
    level = request.GET.get('level')
    if level:
        logs = logs.filter(level=level)
    
    # Пагинация
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'mailings/logs_list.html', {
        'page_obj': page_obj,
        'level': level
    })


@login_required
def user_list(request):
    """Список пользователей сервиса (доступно только менеджерам)"""
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для просмотра списка пользователей.")
        return redirect('dashboard') # Or another appropriate page

    users = User.objects.all().order_by('date_joined')

    return render(request, 'mailings/user_list.html', {'users': users})


@login_required
def user_toggle_block(request, pk):
    """Блокировка/разблокировка пользователя (доступно только менеджерам)""" 
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для блокировки пользователей.")
        return redirect('dashboard')

    user_to_block = get_object_or_404(User, pk=pk)
    if user_to_block != request.user and not user_to_block.is_superuser: # Prevent blocking self or superusers
        user_to_block.is_active = not user_to_block.is_active
        user_to_block.save()
        status = "заблокирован" if not user_to_block.is_active else "разблокирован"
        messages.success(request, f'Пользователь {user_to_block.email} успешно {status}.')
    else:
        messages.error(request, "Невозможно заблокировать этого пользователя.")

    return redirect('user_list')


# You'll need to create templates for user_list.html



def activate(request, uidb64, token):
    """View to activate user account via email link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Basic token check (you might want a more robust method)
    if user is not None and user.email_verification_token == token:
        user.is_active = True # Assuming is_active is used for email confirmation
        user.email_verification_token = '' # Clear token after use
        user.save()
        messages.success(request, 'Ваш email успешно подтвержден. Теперь вы можете войти.')
        return redirect('login') # Redirect to login page
    else:
        messages.error(request, 'Ссылка активации недействительна.')
        return HttpResponse('Ссылка активации недействительна!') # Or render an error page


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'mailings/login.html'
    fields = '__all__'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard')


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('login') # Redirect to login page after logout


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view (request form)"""
    template_name = 'mailings/password_reset_form.html'
    email_template_name = 'mailings/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'mailings/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view (set new password)"""
    template_name = 'mailings/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'mailings/password_reset_complete.html'