#!/usr/bin/env python
"""
Скрипт для запуска системы рассылок
"""
import os

import sys
import subprocess


def run_command(command, description):
    """Запуск команды с выводом описания"""
    print(f"\n{'='*50}")
    print(f"Запуск: {description}")
    print(f"Команда: {command}")
    print(f"{'='*50}")

    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Ошибка при выполнении команды: {exc}")
        return False
    except KeyboardInterrupt:
        print("\nКоманда прервана пользователем")
        return False

    return True


def main():
    """Основная функция запуска"""
    print("🚀 Запуск системы рассылок")
    print("Этот скрипт поможет вам запустить все необходимые компоненты")

    # Проверяем, что мы в правильной директории
    if not os.path.exists('manage.py'):
        print("❌ Ошибка: файл manage.py не найден. "
              "Убедитесь, что вы находитесь в корневой папке проекта.")
        return

    # Проверяем виртуальное окружение
    if not hasattr(sys, 'real_prefix') and not (
           hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):

        print("⚠️  Предупреждение: виртуальное окружение не активировано")
        print("Рекомендуется активировать виртуальное "
              "окружение перед запуском")
        response = input("Продолжить без виртуального окружения? (y/N): ")
        if response.lower() != 'y':
            return

    # Применяем миграции
    print("\n📦 Применение миграций...")
    if not run_command("python manage.py makemigrations", "Создание миграций"):
        return

    if not run_command("python manage.py migrate", "Применение миграций"):
        return

    # Создаем суперпользователя если нужно
    print("\n👤 Создание суперпользователя...")
    response = input("Создать суперпользователя? (y/N): ")
    if response.lower() == 'y':
        run_command("python manage.py createsuperuser",
                    "Создание суперпользователя")

    print("\n✅ Система готова к запуску!")
    print("\nДля запуска всех компонентов выполните "
          "следующие команды в разных терминалах:")
    print("\n1. Django сервер:")
    print("   python manage.py runserver")
    print("\n2. Redis (если не запущен как служба):")
    print("   redis-server")
    print("\n3. Celery worker:")
    print("   celery -A mailing_system worker -l info")
    print("\n4. Celery beat (планировщик):")
    print("   celery -A mailing_system beat -l info")
    print("\n🌐 Веб-интерфейс будет доступен по адресу: http://127.0.0.1:8000/")


if __name__ == "__main__":
    main()
