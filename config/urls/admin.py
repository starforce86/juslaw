from django.contrib import admin
from django.urls import path

# ADMIN urls

urlpatterns = [
    path('admin/', admin.site.urls),
]
