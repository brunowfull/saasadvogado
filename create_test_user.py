from users.models import Lawyer
from django.contrib.auth.hashers import make_password

username = 'testuser'
email = 'test@example.com'
password = 'testpassword'

try:
    user = Lawyer.objects.get(username=username)
    print(f"User '{username}' already exists. Updating password and ensuring login is enabled.")
    user.password = make_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.enable_login = True # Ensure this is True
    user.save()
except Lawyer.DoesNotExist:
    print(f"Creating new superuser '{username}'.")
    user = Lawyer.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        is_superuser=True,
        is_staff=True,
        is_active=True,
        enable_login=True # Ensure this is True
    )
    user.save()

print(f"Superuser '{username}' created/updated with password '{password}'.")
print(f"Verify: enable_login={user.enable_login}, is_active={user.is_active}, is_superuser={user.is_superuser}")
