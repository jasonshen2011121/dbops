from django.shortcuts import render
from mysql import models
# Create your views here.


def base(request):
    return render(request, 'base.html')


def index(request):
    """
    资产总表视图
    :param request:
    :return:
    """
    instance = models.mysqlIns.objects.all()
    return render(request, 'mysql/index.html', locals())
