from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Client(models.Model):
    """Модель клиента для рассылок"""
    email = models.EmailField(verbose_name='Email')
    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    phone = models.CharField(
        max_length=20, 
        verbose_name='Телефон',
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
            )
        ]
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Mailing(models.Model):
    """Модель рассылки"""
    FREQUENCY_CHOICES = [
        ('once', 'Однократно'),
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('active', 'Активна'),
        ('paused', 'Приостановлена'),
        ('completed', 'Завершена'),
    ]

    title = models.CharField(max_length=200, verbose_name='Название рассылки')
    clients = models.ManyToManyField(Client, verbose_name='Клиенты')
    
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    frequency = models.CharField(
        max_length=10, 
        choices=FREQUENCY_CHOICES, 
        default='once',
        verbose_name='Частота'
    )
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='Статус'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Создатель'
    )
    message_template = models.ForeignKey(
        'MessageTemplate',
        on_delete=models.CASCADE,
        verbose_name='Шаблон сообщения'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    """Модель отправленного сообщения"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка отправки'),
    ]

    mailing = models.ForeignKey(
        Mailing, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name='Рассылка'
    )
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        verbose_name='Клиент'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Время отправки')
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mailing.title} -> {self.client.email}"


class MailingLog(models.Model):
    """Модель логов рассылки"""
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    ]

    mailing = models.ForeignKey(
        Mailing, 
        on_delete=models.CASCADE, 
        related_name='logs',
        verbose_name='Рассылка'
    )
    message = models.TextField(verbose_name='Сообщение')
    level = models.CharField(max_length=20, verbose_name='Уровень')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    server_response = models.TextField(verbose_name='Ответ почтового сервера', blank=True, null=True)

    class Meta:
        verbose_name = 'Лог рассылки'
        verbose_name_plural = 'Логи рассылок'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mailing.title} - {self.level} - {self.created_at}" 


class MessageTemplate(models.Model):
    """Модель шаблона сообщения"""
    subject = models.CharField(max_length=200, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Создатель',
        default=1 # You might want to set a more appropriate default or handle this during creation
    )

    class Meta:
        verbose_name = 'Шаблон сообщения'
        verbose_name_plural = 'Шаблоны сообщений'
        ordering = ['subject']

    def __str__(self):
        return self.subject


