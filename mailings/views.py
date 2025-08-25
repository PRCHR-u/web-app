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
        'recent_mailings': recent_mailings,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'mailings/dashboard.html', context)


@login_required
def client_list(request):
    """Список клиентов"""
    if request.user.is_staff:  # Managers can see all clients
        clients = Client.objects.all().order_by('-created_at')
    else:  # Regular users only see their clients
        clients = Client.objects.filter(owner=request.user).order_by('-created_at')

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
    # Permission check: Managers cannot create clients
    if request.user.is_staff:
        messages.error(request, "Менеджеры не имеют прав для создания клиентов.")
        return redirect('client_list') # Redirect managers away
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user # Assign the logged-in user as the owner
            client.save()
            messages.success(request, 'Клиент успешно создан!')
            return redirect('client_list')
    else:
        form = ClientForm()
    
    return render(request, 'mailings/client_form.html', {'form': form, 'title': 'Создать клиента'})


@login_required
def client_edit(request, pk):
    """Редактирование клиента"""
    if request.user.is_staff:
        client = get_object_or_404(Client, pk=pk)
    else:
        client = get_object_or_404(Client, pk=pk, owner=request.user)
    # Permission check: Only staff can edit clients they don't own
    if not request.user.is_staff and client.owner != request.user:
        messages.error(request, "У вас нет прав для редактирования этого клиента.")
        return redirect('client_list') # Or another appropriate page
    
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
    # Retrieve the client based on user type
    if request.user.is_staff:
        client = get_object_or_404(Client, pk=pk)
    else:
        client = get_object_or_404(Client, pk=pk, owner=request.user)
    # Permission check: Only staff can delete clients they don't own
    if not request.user.is_staff and client.owner != request.user:
        messages.error(request, "У вас нет прав для удаления этого клиента.")
        return redirect('client_list') # Or another appropriate page
    
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
def mailing_create(request):
    """Создание рассылки"""
    if request.user.is_staff:
        mailing = get_object_or_404(Mailing, pk=pk)
    else:
        mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
# Permission check: Only the creator can delete, managers cannot delete others\' mailings
    if not request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, "У вас нет прав для удаления этой рассылки.")
        return redirect('mailing_list') # Or another appropriate page
    
    # Add a similar check for managers after retrieving the object
    if request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, "Менеджеры не могут удалять рассылки, созданные другими пользователями.")
        return redirect('mailing_list') # Or another appropriate page

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
    mailing = get_object_or_404(Mailing, pk=pk)

    # Permission check: Only the creator can edit, managers cannot edit others' mailings
    if mailing.created_by != request.user and not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования этой рассылки.")
    
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
    mailing = get_object_or_404(Mailing, pk=pk)

    # Permission check: Only the creator can delete, managers cannot delete others' mailings
    if mailing.created_by != request.user and not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления этой рассылки.")
        return redirect('mailing_list') # Or another appropriate page
    
    if request.method == 'POST':
        mailing.delete()
        messages.success(request, 'Рассылка успешно удалена!')
        return redirect('mailing_list')
    
    return render(request, 'mailings/mailing_confirm_delete.html', {'mailing': mailing})


@login_required
def mailing_detail(request, pk):
    """Детальная информация о рассылке"""
    # Retrieve mailing based on user type
    if not request.user.is_staff:
        mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
        messages.error(request, "У вас нет прав для просмотра этой рассылки.")
        return redirect('mailing_list') # Redirect if not authorized
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
    """Триггер ручной отправки рассылки. (Доступно только создателю)"""
    mailing = get_object_or_404(Mailing, pk=pk)

    # Permission check: Only the creator can trigger manual send
    if mailing.created_by != request.user:
        messages.error(request, "У вас нет прав для запуска рассылок вручную.")
        return redirect('mailing_detail', pk=pk) # Redirect back to detail page

    if mailing.status == 'active':
        send_mailing_task.delay(mailing.id)
        messages.success(request, f'Рассылка "{mailing.title}" успешно запущена вручную!')
    else:
        messages.error(request, 'Рассылка должна быть активной для ручной отправки.')
    return redirect('mailing_detail', pk=mailing.id)



@login_required
def mailing_disable(request, pk):
    """Отключение рассылки (доступно только менеджерам)"""
    # Permission check: Only managers can disable mailings
    if not request.user.is_staff:
        messages.error(request, "У вас нет прав для отключения рассылок.")
        return redirect('dashboard')  # Redirect to dashboard or mailing list

    mailing = get_object_or_404(Mailing, pk=pk)
    # Change status to 'completed' or a dedicated 'disabled' status if it exists
    mailing.status = 'completed'
    mailing.save()
    messages.success(request, f'Рассылка "{mailing.title}" успешно отключена.')
    return redirect('mailing_list')  # Redirect to mailing list


@login_required
@require_POST
def mailing_send_now(request, pk):
    """Отправка рассылки немедленно (Этот функционал лучше реализовать через send_mailing)"""
    messages.error(request, "Этот функционал устарел. Используйте кнопку 'Запустить вручную'.")
    return redirect('mailing_detail', pk=pk)

    if mailing.status == 'active':
            # Запускаем задачу отправки
            send_mailing_task.delay(mailing.id)
            messages.success(request, 'Рассылка запущена!')
    else:
            messages.error(request, 'Рассылка должна быть активной для отправки.')
    return redirect('mailing_detail', pk=pk)


@login_required
def message_list(request):
    """Список шаблонов сообщений"""
    if request.user.is_staff:
        messages_list = Message.objects.all().order_by('-created_at')
    else:
        messages_list = Message.objects.filter(created_by=request.user).order_by('-created_at')
 
 
    # Пагинация
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
 
    return render(request, 'mailings/message_list.html', {
        'page_obj': page_obj,
    })


@login_required
def message_create(request):
    """Создание шаблона сообщения"""
    # Managers can create message templates, regular users can too.
    # The created_by field is set automatically.
    if request.method == 'POST':
        form = MessageForm(request.POST) # Assuming MessageForm exists for Message model (template)
        if form.is_valid():
            message_template = form.save(commit=False)
            message_template.created_by = request.user # Assign the logged-in user as the creator
            message_template.save()
            messages.success(request, 'Шаблон сообщения успешно создан!')
            return redirect(reverse_lazy('message_list')) # Redirect to the message list page
    else:
        form = MessageForm() # Assuming MessageForm exists for Message model (template)

    return render(request, 'mailings/message_form.html', {
        'form': form,
        'title': 'Создать шаблон сообщения'
    })


@login_required
def message_detail(request, pk):
    """Детальная информация о шаблоне сообщения"""
    # Retrieve message template based on user type
    if request.user.is_staff:
        message_template = get_object_or_404(Message, pk=pk)
    else:
        message_template = get_object_or_404(Message, pk=pk, created_by=request.user)
    
    return render(request, 'mailings/message_detail.html', {
        'message_template': message_template,
    })


@login_required
def message_edit(request, pk):
    """Редактирование шаблона сообщения"""
    # Retrieve template based on user type
    if request.user.is_staff:
        message_template = get_object_or_404(Message, pk=pk)
    else:
        message_template = get_object_or_404(Message, pk=pk, created_by=request.user)

    # Permission check: Only the creator can edit, managers cannot edit others' templates
    if message_template.created_by != request.user and not request.user.is_staff:
        messages.error(request, "У вас нет прав для редактирования этого шаблона сообщения.")
        return redirect(reverse_lazy('message_list')) # Or another appropriate page

    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message_template) # Assuming MessageForm exists
        if form.is_valid():
            form.save()
            messages.success(request, 'Шаблон сообщения успешно обновлен!')
            return redirect(reverse_lazy('message_list')) # Redirect to list
    else:
        form = MessageForm(instance=message_template) # Assuming MessageForm exists

    return render(request, 'mailings/message_form.html', {
        'form': form,
        'title': 'Редактировать шаблон сообщения',
        'message_template': message_template,
    })


@login_required
def message_delete(request, pk):
    """Удаление шаблона сообщения"""
    # Retrieve template based on user type
    if request.user.is_staff:
        message_template = get_object_or_404(Message, pk=pk)
    else:
        message_template = get_object_or_404(Message, pk=pk, created_by=request.user)

    # Permission check: Only the creator can delete, managers cannot delete others' templates
    if message_template.created_by != request.user and not request.user.is_staff:
        messages.error(request, "У вас нет прав для удаления этого шаблона сообщения.")
        return redirect(reverse_lazy('message_list')) # Or another appropriate page

    if request.method == 'POST':
        message_template.delete()
        messages.success(request, 'Шаблон сообщения успешно удален!')
        return redirect(reverse_lazy('message_list')) # Redirect to list

    return render(request, 'mailings/message_confirm_delete.html', {
        'message_template': message_template,
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


@login_required
def user_mailing_reports(request):
    """Страница отчетов по рассылкам пользователя"""

    # Retrieve data for the current user's mailings
    user_mailings = Mailing.objects.filter(created_by=request.user)
    total_mailings = user_mailings.count()

    # Get all sent messages related to the user's mailings
    user_sent_messages = SentMessage.objects.filter(mailing__created_by=request.user)
    total_sent_messages = user_sent_messages.count()
    successful_messages = user_sent_messages.filter(status='sent').count()
    failed_messages = user_sent_messages.filter(status='failed').count()

    context = {
        'total_mailings': total_mailings,
        'total_sent_messages': total_sent_messages,
        'successful_messages': successful_messages,
        'failed_messages': failed_messages,
        # Add more data as needed for reporting (e.g., trends, specific mailing stats)
    }

    return render(request, 'mailings/user_reports.html', context)


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