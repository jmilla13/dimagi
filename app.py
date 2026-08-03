from django.core.management import execute_from_command_line
import os


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "location_form.settings")
    execute_from_command_line(["manage.py"] + __import__("sys").argv[1:])
