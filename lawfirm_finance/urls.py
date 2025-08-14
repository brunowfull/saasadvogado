from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('dashboard/', include('dashboard.urls')),
    path('logout/', views.custom_logout, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]