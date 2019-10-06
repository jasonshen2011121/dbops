from django.urls import include, path
from . import views

app_name = 'mysql'

urlpatterns = [
    path('login/', views.login),
    path('index/', views.index),
    path('register/', views.register),
    path('submitSql/<str:ins_name>/', views.submitSql,name='submitSql'),
    ]