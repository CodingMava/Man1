import os
import sys
from pathlib import Path

# Add parent dir to sys.path so we can import 'finance' as a module and access 'settings'
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Load .env file manually if it exists in parent directory
env_path = BASE_DIR / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, value = line.strip().split('=', 1)
                    os.environ.setdefault(key, value)
                except ValueError:
                    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    execute_from_command_line(sys.argv)
