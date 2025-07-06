import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'glam_hex'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glam_hex.settings')

from glam_hex.wsgi import application

app = application