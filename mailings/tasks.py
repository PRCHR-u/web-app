from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import Mailing, Message, MailingLog, Client

logger = logging.getLogger(__name__)


@shared_task
def send_mailing_task(mailing_id):
    """Задача для отправки рассылки"""
    try:
        mailing = Mailing.objects.get(id=mailing_id)
        
        # Проверяем, что рассылка активна и время подходящее
        now = timezone.now()
        if mailing.status != 'active' or now < mailing.start_time or now > mailing.end_time:
            logger.warning(f"Рассылка {mailing_id} не может быть отправлена: статус={mailing.status}, время={now}")
            return
        
        # Получаем клиентов для рассылки
        clients = mailing.clients.all()
        
        # Создаем записи сообщений для каждого клиента
        messages_to_send = []
        for client in clients:
            # Проверяем, не было ли уже отправлено сообщение этому клиенту
            existing_message = Message.objects.filter(
                mailing=mailing,
                client=client,
                status='sent'
            ).first()
            
            if not existing_message:
                message = Message.objects.create(
                    mailing=mailing,
                    client=client,
                    status='pending'
                )
                messages_to_send.append(message)
        
        # Отправляем сообщения
        sent_count = 0
        failed_count = 0
        
        for message in messages_to_send:
            log_status = 'failed'
            log_message = ''
            try:
                # Отправляем email
                server_response = send_mail(
                    subject=mailing.message_template.subject,
                    message=mailing.message_template.body,
                    fail_silently=False,
                )
                
                # Обновляем статус сообщения
                message.status = 'sent'
                message.sent_at = timezone.now()
                message.save()
                
                sent_count += 1
                
                # Логируем успешную отправку
                log_status = 'success'
                log_message = f"Сообщение отправлено клиенту {message.client.email}"
                
            except Exception as e: # Catching a broad exception for demonstration; refine as needed
                # Обновляем статус сообщения на ошибку
                message.status = 'failed'
                message.error_message = str(e)
                message.save()
                
                failed_count += 1
                
                # Логируем ошибку
                log_status = 'failed'
                log_message = f"Ошибка отправки клиенту {message.client.email}: {str(e)}"
                server_response = str(e) # Store the exception as the server response
                
                logger.error(f"Ошибка отправки сообщения {message.id}: {str(e)}")

            MailingLog.objects.create(
                mailing=mailing,
                message=log_message,
                status=log_status,
                server_response=server_response if 'server_response' in locals() else '', # Ensure server_response is defined
            )
        
        # Логируем итоги рассылки

        
        logger.info(f"Рассылка {mailing_id} завершена. Отправлено: {sent_count}, Ошибок: {failed_count}")
        
    except Mailing.objects.DoesNotExist:
        logger.error(f"Рассылка {mailing_id} не найдена")
    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки {mailing_id}: {str(e)}")
        
        # Логируем общую ошибку
        try:
            mailing = Mailing.objects.get(id=mailing_id)
            MailingLog.objects.create(
                mailing=mailing,
                message=f"Общая ошибка рассылки: {str(e)}",
                status='failed',
                server_response=str(e),
            )
        except:
            pass


@shared_task
def check_scheduled_mailings():
    """Задача для проверки и запуска запланированных рассылок"""
    now = timezone.now()
    
    # Находим активные рассылки, которые нужно запустить
    mailings_to_send = Mailing.objects.filter(
        status='active',
        start_time__lte=now,
        end_time__gte=now
    )
    
    for mailing in mailings_to_send:
        # Проверяем, нужно ли отправлять рассылку сейчас
        if should_send_mailing_now(mailing, now):
            send_mailing_task.delay(mailing.id)
            logger.info(f"Запущена запланированная рассылка {mailing.id}")


def should_send_mailing_now(mailing, now):
    """Проверяет, нужно ли отправлять рассылку сейчас"""
    if mailing.frequency == 'once':
        # Для однократных рассылок проверяем, была ли уже отправка
        return not Message.objects.filter(mailing=mailing, status='sent').exists()
    
    elif mailing.frequency == 'daily':
        # Для ежедневных рассылок проверяем, была ли отправка сегодня
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return not Message.objects.filter(
            mailing=mailing,
            status='sent',
            sent_at__gte=today_start,
            sent_at__lt=today_end
        ).exists()
    
    elif mailing.frequency == 'weekly':
        # Для еженедельных рассылок проверяем, была ли отправка на этой неделе
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        return not Message.objects.filter(
            mailing=mailing,
            status='sent',
            sent_at__gte=week_start,
            sent_at__lt=week_end
        ).exists()
    
    elif mailing.frequency == 'monthly':
        # Для ежемесячных рассылок проверяем, была ли отправка в этом месяце
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            month_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return not Message.objects.filter(
            mailing=mailing,
            status='sent',
            sent_at__gte=month_start,
            sent_at__lt=month_end
        ).exists()
    
    return False


@shared_task
def cleanup_old_logs():
    """Задача для очистки старых логов"""
    # Удаляем логи старше 30 дней
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = MailingLog.objects.filter(created_at__lt=cutoff_date).delete()[0]
    
    logger.info(f"Удалено {deleted_count} старых логов")
    
    return deleted_count 