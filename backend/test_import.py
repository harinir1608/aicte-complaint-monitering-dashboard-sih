import sys, os
sys.path.insert(0, '.')
from app.core.config import settings
print('Settings loaded OK')
print('DB URL:', settings.DATABASE_URL[:40])
print('Environment:', settings.ENVIRONMENT)
from app.models.user import User
from app.models.institution import Institution
from app.models.complaint import Complaint
from app.models.case import Case
from app.models.overlap import OverlapAlert
print('All models imported OK')
from app.core.security import hash_password, verify_password
h = hash_password('TestPass@123')
assert verify_password('TestPass@123', h)
print('Password hashing OK')
from app.api.v1.endpoints.auth import router as auth_router
print('Auth router OK')
print('\n✅ Backend core imports successful!')
