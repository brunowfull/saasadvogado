from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

@login_required
def custom_logout(request):
    """
    Custom logout view that ensures proper logout and redirect behavior.
    """
    logout(request)
    return redirect('login')