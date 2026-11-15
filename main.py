import os
import sys

def run():
    """Inicia as migrações e o servidor de desenvolvimento do Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "littlecars_config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc

    # Garante que as migrações e dados seed estejam aplicados
    print("🏎️ Verificando e aplicando migrações do Django...")
    execute_from_command_line(["manage.py", "migrate", "--noinput"])

    # Inicia o servidor HTTP
    print("🚀 Iniciando LittleCars em http://127.0.0.1:8000 ...")
    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000"])

if __name__ == "__main__":
    run()
