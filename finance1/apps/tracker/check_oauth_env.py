import os
# Load .env file manually
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, val = line.strip().split('=', 1)
                    os.environ.setdefault(key, val)
                except ValueError:
                    pass

cid = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
sec = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

print(f"Client ID Found: {bool(cid)}")
if cid: print(f"Client ID Starts With: {cid[:5]}...")
print(f"Client Secret Found: {bool(sec)}")
if sec: print(f"Client Secret Starts With: {sec[:3]}...")
