from django.urls import include, path
from . import views

app_name = 'mysql'

urlpatterns = [
    path('login/', views.login),
    path('index/', views.index),
    path('register/', views.register),
    path('submitSql/', views.submitSql),
    path('test/<int:id>/', views.test, name='test'),
    ]