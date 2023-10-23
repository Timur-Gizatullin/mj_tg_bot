"""
WSGI config for t_bot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")

application = get_wsgi_application()
application = WhiteNoise(application, root="/path/to/static/files")
application.add_files("/path/to/more/static/files", prefix="more-files/")
