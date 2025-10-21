from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('logout/', views.user_logout, name='logout'),
    path('auth/', views.auth_view, name='auth'),

]