
from django.shortcuts import render
from django.shortcuts import redirect
from .utils import *
from . import models
from . import forms
# Create your views here.
import hashlib
import datetime
from django.conf import settings

def send_email(email, code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自dba的注册确认邮件'

    text_content = '''注册确认请点击！\
                    如有问题，请联系dba！'''

    html_content = '''
                    <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>www.dba.com</a>，\
                    xxx</p>
                    <p>请点击站点链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format('127.0.0.1:8888', code, settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    models.ConfirmString.objects.create(code=code, user=user,)
    return code

def hash_code(s, salt='mysite'):# 加点盐
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()

def index(request):
    if not request.session.get('is_login', None):
        return redirect('/mysql/login')
    return render(request, 'mysql/index.html')


def login(request):
    message = ''
    if request.session.get('is_login', None):  # 不允许重复登录
        return redirect('/mysql/index/')
    if request.method == "POST":
      login_form = forms.UserForm(request.POST)
      message = '请检查填写的内容！'
      if login_form.is_valid():

        username = login_form.cleaned_data.get('username')
        password = login_form.cleaned_data.get('password')
        print(username, password)
        try:
          user = models.User.objects.get(username=username)
          print (user.password)
          print (hash_code(password))
          if user.password == hash_code(password):
            print (hash_code(password))
            print (request.session)
            request.session['is_login'] = True
            #request.session['user_id'] = user.id
            #request.session['user_name'] = user.name
            return redirect('/mysql/index/')
          else:
            message='密码不正确'
        except:
          try:
            ldapAuth = LdapAuth(username, password)
            login_mark = ldapAuth.ldap_auth()
            print (login_mark)
            print(request.session)

            if login_mark == 'success':
              print ('ahahhahaha')
              request.session['is_login'] = True
              #request.session['user_id'] = user.id
              #request.session['user_name'] = user.username
              return redirect('/mysql/index/')
            else:
              message='密码不正确'
          except:
            message = 'has exception'
            render(request, 'mysql/login.html', locals())
    print (locals())
    print (message)
    login_form = forms.UserForm()
    return render(request, 'mysql/login.html', locals())


def register(request):
    if request.session.get('is_login', None):
        return redirect('/mysql/index/')

    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')

            if password1 != password2:
                message = '两次输入的密码不同！'
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = models.User.objects.filter(name=username)
                if same_name_user:
                    message = '用户名已经存在'
                    return render(request, 'login/register.html', locals())
                same_email_user = models.User.objects.filter(email=email)
                if same_email_user:
                    message = '该邮箱已经被注册了！'
                    return render(request, 'login/register.html', locals())

                new_user = models.User()
                new_user.name = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                code = make_confirm_string(new_user)
                send_email(email, code)

                message = '请前往邮箱进行确认！'
                return render(request, 'login/confirm.html', locals())
        else:
            return render(request, 'login/register.html', locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())

def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求!'
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = datetime.datetime.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = '您的邮件已经过期！请重新注册!'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登录！'
        return render(request, 'login/confirm.html', locals())

def logout(request):
    if not request.session.get('is_login', None):
        # 如果本来就未登录，也就没有登出一说
        return redirect("mysql/login/")
    request.session.flush()
    # 或者使用下面的方法
    # del request.session['is_login']
    # del request.session['user_id']
    # del request.session['user_name']
    return redirect("/mysql/login/")
