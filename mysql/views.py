
from django.shortcuts import render
from django.shortcuts import redirect
from .utils import *
from .models import mysqlIns
from . import forms
# Create your views here.
import hashlib
import datetime
from django.conf import settings
from collections import OrderedDict
from . import models
from .dao import Dao
dao = Dao()
from django.http import HttpResponse, HttpResponseRedirect

# 提交SQL的页面
# 输入参数为实例名，通过http post过来，所以前面一个form的发送为实例名

def gotosqlpage(request, instance_name):
    dictAllClusterDb = OrderedDict()
    ins_model = mysqlIns.objects.filter(instance_name=instance_name)
    host = ins_model[0].address
    port = 3306
    user = ins_model[0].user
    pwd  = ins_model[0].pwd

    try:
        listDb = dao.getAlldbByCluster(host, port, user, pwd)
        dictAllClusterDb[instance_name] = listDb
        print (listDb)
    except Exception as msg:
        dictAllClusterDb[instance_name] = [str(msg)]
    dictAllClusterDb=dictAllClusterDb[instance_name]
    context = {'dictAllClusterDb': dictAllClusterDb}
    return render(request, 'mysql/test.html', locals())

def autoreview(request):
    workflowid = request.POST.get('workflowid')
    sqlContent = request.POST['sql_content']
    workflowName = request.POST['workflow_name']
    clusterName = request.POST['cluster_name']
    isBackup = request.POST['is_backup']
    reviewMan = request.POST['review_man']
    subReviewMen = request.POST.get('sub_review_man', '')
    listAllReviewMen = (reviewMan, subReviewMen)

    # 服务器端参数验证
    if sqlContent is None or workflowName is None or clusterName is None or isBackup is None or reviewMan is None:
        context = {'errMsg': '页面提交参数可能为空'}
        return render(request, 'error.html', context)
    sqlContent = sqlContent.rstrip()
    if sqlContent[-1] != ";":
        context = {'errMsg': "SQL语句结尾没有以;结尾，请后退重新修改并提交！"}
        return render(request, 'error.html', context)

    # 交给inception进行自动审核
    try:
        result = inceptionDao.sqlautoReview(sqlContent, clusterName)
    except Exception as msg:
        context = {'errMsg': msg}
        return render(request, 'error.html', context)
    if result is None or len(result) == 0:
        context = {'errMsg': 'inception返回的结果集为空！可能是SQL语句有语法错误'}
        return render(request, 'error.html', context)
    # 要把result转成JSON存进数据库里，方便SQL单子详细信息展示
    jsonResult = json.dumps(result)

    # 遍历result，看是否有任何自动审核不通过的地方，一旦有，则为自动审核不通过；没有的话，则为等待人工审核状态
    workflowStatus = Const.workflowStatus['manreviewing']
    for row in result:
        if row[2] == 2:
            # 状态为2表示严重错误，必须修改
            workflowStatus = Const.workflowStatus['autoreviewwrong']
            break
        elif re.match(r"\w*comments\w*", row[4]):
            workflowStatus = Const.workflowStatus['autoreviewwrong']
            break

    # 存进数据库里
    engineer = request.session.get('login_username', False)
    if not workflowid:
        Workflow = workflow()
        Workflow.create_time = timezone.now()
    else:
        Workflow = workflow.objects.get(id=int(workflowid))
    Workflow.workflow_name = workflowName
    Workflow.engineer = engineer
    Workflow.review_man = json.dumps(listAllReviewMen, ensure_ascii=False)
    Workflow.status = workflowStatus
    Workflow.is_backup = isBackup
    Workflow.review_content = jsonResult
    Workflow.cluster_name = clusterName
    Workflow.sql_content = sqlContent
    Workflow.execute_result = ''
    Workflow.audit_remark = ''
    Workflow.save()
    workflowId = Workflow.id

    # 自动审核通过了，才发邮件
    if workflowStatus == Const.workflowStatus['manreviewing']:
        # 如果进入等待人工审核状态了，则根据settings.py里的配置决定是否给审核人发一封邮件提醒.
        if hasattr(settings, 'MAIL_ON_OFF') == True:
            if getattr(settings, 'MAIL_ON_OFF') == "on":
                url = getDetailUrl(request) + str(workflowId) + '/'

                # 发一封邮件
                strTitle = "新的SQL上线工单提醒 # " + str(workflowId)
                strContent = "发起人：" + engineer + "\n审核人：" + str(
                    listAllReviewMen) + "\n工单地址：" + url + "\n工单名称： " + workflowName + "\n具体SQL：" + sqlContent
                reviewManAddr = [email['email'] for email in
                                 users.objects.filter(username__in=listAllReviewMen).values('email')]
                mailSender.sendEmail(strTitle, strContent, reviewManAddr)
            else:
                # 不发邮件
                pass

    return HttpResponseRedirect(reverse('sql:detail', args=(workflowId,)))

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


def test(request,ins_name):
    ins_name = ins_name
    return render(request, 'mysql/test.html',locals())

def index(request):
    """
    资产总表视图
    :param request:
    :return:
    """
    if not request.session.get('is_login', None):
        return redirect('/mysql/login')
    instance = mysqlIns.objects.all()
    return render(request, 'mysql/index.html', locals())


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
