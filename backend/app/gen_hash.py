import sys, json
sys.path.insert(0, '/app')
from passlib.context import CryptContext
h = CryptContext(schemes=['bcrypt'], deprecated='auto').hash('admin123')
import os
print(json.dumps({'hash': h}))
sys.stdout.flush()
