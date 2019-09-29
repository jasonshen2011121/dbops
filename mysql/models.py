from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class mysqlIns(models.Model):
    """服务器设备"""

    isslave_choice = (
        (0, '主库'),
        (1, '从库'),
    )

    created_by_choice = (
        ('auto', '自动添加'),
        ('manual', '手工录入'),
    )
    instance_name = models.CharField(max_length=128, null=True, blank=True, verbose_name='实例名')
    address = models.CharField(max_length=512, blank=True, null=True, verbose_name='实例地址')
    #isslave = models.CharField(choices=isslave_choice, max_length=32, default=0, verbose_name="是否主从")
    created_by = models.CharField(choices=created_by_choice, max_length=32, default='auto', verbose_name="添加方式")
    version = models.CharField('数据库版本', max_length=64, blank=True, null=True)


    def __str__(self):
        return self.instance_name
