from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .models import Client, Mailing, Message, MailingLog
from .forms import ClientForm, MailingForm, UserRegistrationForm, MailingFilterForm
from .tasks import send_mailing_task


def register(request):
    """Регистрация пользователей"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'mailings/register.html', {'form': form})


@login_required
def dashboard(request):
    """Главная страница с дашбордом"""
    # Статистика
    total_mailings = Mailing.objects.filter(created_by=request.user).count()
    active_mailings = Mailing.objects.filter(created_by=request.user, status='active').count()
    total_clients = Client.objects.count()
    total_messages = Message.objects.filter(mailing__created_by=request.user).count()
    
    # Последние рассылки
    recent_mailings = Mailing.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    
    # Последние сообщения
    recent_messages = Message.objects.filter(mailing__created_by=request.user).select_related('mailing', 'client').order_by('-created_at')[:10]
    
    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'total_clients': total_clients,
        'total_messages': total_messages,
        'recent_mailings': recent_mailings,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'mailings/dashboard.html', context)


@login_required
def client_list(request):
    """Список клиентов"""
    clients = Client.objects.all().order_by('-created_at')
    
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
            form.save()
            messages.success(request, 'Клиент успешно создан!')
            return redirect('client_list')
    else:
        form = ClientForm()
    
    return render(request, 'mailings/client_form.html', {'form': form, 'title': 'Создать клиента'})


@login_required
def client_edit(request, pk):
    """Редактирование клиента"""
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
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Клиент успешно удален!')
        return redirect('client_list')
    
    return render(request, 'mailings/client_confirm_delete.html', {'client': client})


@login_required
def mailing_list(request):
    """Список рассылок"""
    mailings = Mailing.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Фильтрация
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
    if request.method == 'POST':
        form = MailingForm(request.POST)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.created_by = request.user
            mailing.save()
            form.save_m2m()  # Сохраняем связи many-to-many
            
            messages.success(request, 'Рассылка успешно создана!')
            return redirect('mailing_list')
    else:
        form = MailingForm()
    
    return render(request, 'mailings/mailing_form.html', {
        'form': form, 
        'title': 'Создать рассылку'
    })


@login_required
def mailing_edit(request, pk):
    """Редактирование рассылки"""
    mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = MailingForm(request.POST, instance=mailing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рассылка успешно обновлена!')
            return redirect('mailing_list')
    else:
        form = MailingForm(instance=mailing)
    
    return render(request, 'mailings/mailing_form.html', {
        'form': form, 
        'title': 'Редактировать рассылку',
        'mailing': mailing
    })


@login_required
def mailing_delete(request, pk):
    """Удаление рассылки"""
    mailing = get_object_or_404(Mailing, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        mailing.delete()
        messages.success(request, 'Рассылка успешно удалена!')
        return redirect('mailing_list')
    
    return render(request, 'mailings/mailing_confirm_delete.html', {'mailing': mailing})


@login_required
def mailing_detail(request, pk):
    """Детальная информация о рассылке"""
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
def mailing_send_now(request, pk):
    """Отправка рассылки немедленно"""
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