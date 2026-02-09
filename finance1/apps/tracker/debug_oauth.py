import os
import django
from django.conf import settings

# Setup Django environment
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    print(f"Loading .env from {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, val = line.strip().split('=', 1)
                    os.environ.setdefault(key, val)
                except ValueError:
                    pass
else:
    print("WARNING: No .env file found in project root")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
django.setup()

def debug_oauth():
    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', None)
    
    print("-" * 30)
    print(f"GOOGLE_OAUTH_CLIENT_ID: {'SET' if client_id else 'NOT SET'}")
    if client_id:
        print(f"  Value (first 10 chars): {client_id[:10]}...")
    
    print(f"GOOGLE_OAUTH_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
    if client_secret:
        print(f"  Value (first 3 chars): {client_secret[:3]}...")
        
    print("-" * 30)
    print("Redirect URI Configuration:")
    print("Ensure your Google Cloud Console has this EXACT URI added to 'Authorized redirect URIs':")
    print("http://127.0.0.1:8000/oauth/google/callback/")
    print("(OR http://localhost:8000/oauth/google/callback/ depending on how you access the site)")
    print("-" * 30)

if __name__ == '__main__':
    debug_oauth()
