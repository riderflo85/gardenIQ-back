"""Settings for Django Paths"""

from pathlib import Path

DJANGO_ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT_DIR = DJANGO_ROOT_DIR.parent
