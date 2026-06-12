from app.core.security import hash_password

password = "Test1234"
print(f"Testing password: {password}")
print(f"Length: {len(password)}")
print(f"Bytes: {len(password.encode('utf-8'))}")

try:
    hashed = hash_password(password)
    print(f"SUCCESS: Hash generated")
    print(f"Hash: {hashed[:50]}...")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
