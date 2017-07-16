#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import collections
import json
import locale
import re
import subprocess
import urllib

import jdatetime
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaulttags import register
from django.utils import timezone

from .models import Announcement, Contest, Participant


# Create your views here.

# @login_required(login_url="login/")
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def password_check(password):
    """
    Verify the strength of 'password'
    Returns a dict indicating the wrong criteria
    A password is considered strong if:
        8 characters length or more
        1 digit or more
        1 symbol or more
        1 uppercase letter or more
        1 lowercase letter or more
    """

    # calculating the length
    length_error = len(password) < 8

    # searching for digits
    digit_error = re.search(r"\d", password) is None

    # searching for uppercase
    uppercase_error = re.search(r"[A-Z]", password) is None

    # searching for lowercase
    lowercase_error = re.search(r"[a-z]", password) is None

    # searching for symbols
    symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', password) is None

    # overall result
    password_ok = not (length_error or digit_error or (uppercase_error and lowercase_error))

    return {
        'password_ok': password_ok,
        'length_error': length_error,
        'digit_error': digit_error,
        'uppercase_error': uppercase_error,
        'lowercase_error': lowercase_error,
        'symbol_error': symbol_error,
    }


def index(request):
    All = Announcement.objects.all()
    print(request.user.is_authenticated() == True)
    print(request.user)
    return render(request, "cms_register/index.html", {'Announce': All})


def loginv(request):
    usern = None
    passw = None
    ok = False
    if request.method == 'POST':
        usern = request.POST['username']
        passw = request.POST['password']
        ok = True
    user = authenticate(username=usern, password=passw)
    print(request.user.is_authenticated() == True)
    if user is not None or request.user.is_authenticated():
        login(request, user)
        return redirect('cms_register:index')
    else:
        return render(request, "cms_register/login.html", {'Error': ok})


def logoutv(request):
    logout(request)
    return redirect('cms_register:index')


def profile(request):
    return register(request, 1)


def register(request, x=0):
    info = collections.OrderedDict()
    error = {}
    done = False
    cap_error = False

    def getInfo(field):
        if field in request.POST and request.POST[field] != '':
            return request.POST[field]
        else:
            return None

    def addError(field, val):
        if error[field] == '':
            error[field] = val

    if request.user.is_authenticated() and not x:
        return redirect('cms_register:index')
    if not request.user.is_authenticated() and x:
        return redirect('cms_register:index')
    fields = ['username', 'email', 'password', 'password2', 'name', 'lname']
    place = {'username': 'نام کاربری',
             'email': 'رایانامه',
             'password': 'رمزعبور',
             'password2': 'تکرار رمزعبور',
             'name': 'نام',
             'lname': 'نام خانوادگی',
             # 'grade' : 'پایه',
             # 'school' : 'مدرسه',
             }
    types = {'username': 'text',
             'email': 'email',
             'password': 'password',
             'password2': 'password',
             'name': 'text',
             'lname': 'text',
             # 'grade' : 'text',
             # 'school' : 'text',
             }
    for field in fields:
        error[field] = ''
        info[field] = ''
    if x:
        info['username'] = request.user.username
        info['name'] = request.user.first_name
        info['lname'] = request.user.last_name
        info['email'] = request.user.email
    if request.method == 'POST':
        for field in fields:
            if getInfo(field) == None:
                if not x or (field != 'password' and field != 'password2' and field != 'username'):
                    addError(field, 'این فیلد لازم است.')
            else:
                info[field] = getInfo(field)
        if x:
            info['username'] = request.user.username
        if len(info['username']) > 150:
            addError('username', 'حداکثر ۱۵۰ کاراکتر')
        if not re.match("^[A-Za-z0-9_-]+$", info['username']):
            addError('username', 'تنها حروف انگلیسی، ارقام، خط تیره و آندرلاین مجاز است.')
        if not x and User.objects.filter(username=info['username']).exists():
            addError('username', 'این نام کاربری انتخاب شده است.')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", info['email']):
            addError('email', 'ایمیل معتبر وارد کنید.')
        if info['password'] != '' or info['password2'] != '':
            passdet = password_check(info['password'])
            if passdet['length_error']:
                addError('password', 'حداقل ۸ کاراکتر ضروری است.')
            if passdet['digit_error']:
                addError('password', 'حداقل یک کاراکتر رقم ضروری است.')
            if passdet['lowercase_error'] and passdet['uppercase_error']:
                addError('password', 'حداقل یک حرف لاتین ضروری است.')
            if info['password'] != info['password2']:
                addError('password2', 'با رمز عبور مطابقت ندارد.')
        if not re.match(r"^[a-zA-Z ]+$", info['name']):
            addError('name', 'نام خود را انگلیسی وارد کنید.(حروف و فاصله)')
        if not re.match(r"^[a-zA-Z ]+$", info['lname']):
            addError('lname', 'نام خانوادگی خود را انگلیسی وارد کنید.(حروف و فاصله)')
        ok = True
        for key in error:
            if error[key] != '':
                ok = False;
        values = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': request.POST.get(u'g-recaptcha-response', None),
            'remoteip': request.META.get("REMOTE_ADDR", None),
        }
        url = settings.RECAPTCHA_REQUEST_URL
        data = urllib.parse.urlencode(values)
        binary_data = data.encode('UTF-8')
        req = urllib.request.Request(url, binary_data)
        resp = urllib.request.urlopen(req)
        strfeedback = resp.read().decode('UTF-8')
        res = json.loads(strfeedback)
        if not res['success']:
            ok = False
            cap_error = True;
        if ok and not x:
            user = User.objects.create_user(info['username'], info['email'], info['password'])
            user.first_name = info['name']
            user.last_name = info['lname']
            # user.contestant.grade = info['grade']
            # user.contestant.school = info['school']
            user.save()
            res = subprocess.call(
                ['cmsAddUser', '-p', info['password'], '-e', info['email'], info['name'], info['lname'],
                 info['username']])
            if not res:
                subprocess.call(
                    ['python', 'python/EditUser.py', '-p', info['password'], '-e', info['email'], '-fn', info['name'],
                     '-ln', info['lname'], info['username']])
            done = True
        if ok and x:
            user = User.objects.get(username=info['username'])
            user.first_name = info['name']
            user.last_name = info['lname']
            user.email = info['email']
            if info['password'] != '':
                user.set_password(info['password'])
                subprocess.call(
                    ['python', 'python/EditUser.py', '-p', info['password'], '-e', info['email'], '-fn', info['name'],
                     '-ln', info['lname'], info['username']])
            else:
                subprocess.call(
                    ['python', 'python/EditUser.py', '-e', info['email'], '-fn', info['name'], '-ln', info['lname'],
                     info['username']])
            user.save()
            done = True
    info['password'] = info['password2'] = ''
    return render(request, "cms_register/register.html",
                  {'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY, 'ok': done, 'info': info, 'error': error,
                   'place': place, 'type': types, 'caper': cap_error, 'x': x})


l2p = [u'۰', u'۱', u'۲', u'۳', u'۴', u'۵', u'۶', u'۷', u'۸', u'۹']


def persian_num(value):
    if isinstance(value, int):
        value = str(value)
    for i in range(10):
        value = value.replace(str(i), l2p[i])
    return value


def format_timedelta(td, type):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours, minutes, seconds = int(days), int(hours), int(minutes), int(seconds)
    if type != 2:
        if hours < 10:
            hours = '0%s' % int(hours)
        if minutes < 10:
            minutes = '0%s' % minutes
        if seconds < 10:
            seconds = '0%s' % seconds
        if type == 1:
            return '%s:%s' % (hours, minutes)
        else:
            return '%s:%s:%s' % (hours, minutes, seconds)
    if hours == 0:
        return '%s روز' % (days)
    return '%s روز و %s ساعت' % (days, hours)


def contest_view(request):
    done = False
    if request.method == 'POST' and request.user.is_authenticated() and request.POST.get('register') == 'register':
        cid = request.POST.get('cid');
        con = Contest.objects.get(id=cid);
        if Participant.objects.filter(user=request.user, contest=con).count() == 0:
            partof = Participant(user=request.user, contest=con)
            partof.save()
            subprocess.call(['cmsAddParticipation', '-c', str(con.cms_id), request.user.username])
            done = True
    clist = Contest.objects.order_by('-start_time')
    date = {}
    time = {}
    expired = {}
    ended = {}
    registered = {}
    dur = {}
    need = {}
    cdown = {}
    locale.setlocale(locale.LC_ALL, 'fa_IR')
    for contest in clist:
        cdown[contest.id] = max(0, int((contest.start_time - timezone.now() + contest.duration).total_seconds()))
        tmp = jdatetime.datetime.fromgregorian(datetime=timezone.localtime(contest.start_time))
        date[contest.id] = persian_num(tmp.strftime("%d %b %Y"))
        time[contest.id] = persian_num(tmp.strftime("%H:%M"))
        dur[contest.id] = persian_num(format_timedelta(contest.duration, 2))
        need[contest.id] = persian_num(format_timedelta(contest.contest_time, 1))
        expired[contest.id] = (timezone.now() > (contest.start_time + contest.duration))
        print(timezone.now())
        print(contest.start_time + contest.duration)
        ended[contest.id] = (timezone.now() > (contest.start_time + contest.contest_time))
        registered[contest.id] = False
        if request.user.is_authenticated() and contest.participant_set.filter(user=request.user).count() > 0:
            registered[contest.id] = True
    return render(request, "cms_register/contests.html",
                  {'contests': clist, 'date': date, 'time': time, 'expired': expired, 'registered': registered,
                   'done': done, 'dur': dur, 'need': need, 'ended': ended, 'cdown': cdown})


def comp(a, b):
    if (a['subs'][-1]['score'] > b['subs'][-1]['score']):
        return -1
    elif (a['subs'][-1]['score'] < b['subs'][-1]['score']):
        return 1
    else:
        if (a['name'].lower() < b['name'].lower()):
            return -1
        else:
            return 1


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'

    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def unrank(request, contest_id):
    return ranking(request, contest_id, True)


def ranking(request, contest_id, unof=False):
    contest = get_object_or_404(Contest, id=contest_id)
    expired = (timezone.now() > (contest.start_time + contest.contest_time))
    if unof:
        expired = (timezone.now() > (contest.start_time + contest.duration))
    rank = contest.ranking_file
    if unof:
        rank = contest.unofficial_ranking_file
    if not rank:
        return render(request, "cms_register/ranking.html", {'error': True})
    users = rank.readlines()
    head = users[0].decode().replace('\n', '').split('\t')
    head[0] = '#';
    mx = users[1].decode().replace('\n', '').split('\t')
    for i in range(len(mx)):
        mx[i] = float(mx[i])
    users = users[2:]
    tab = []
    mxg = 128
    for user in users:
        th = {}
        li = user.decode().replace('\n', '').split('\t')
        th['name'] = li[1]
        res = []
        ret = li[2:]
        for i in range(len(ret)):
            inf = {}
            ret[i] = float(ret[i])
            inf['score'] = int(ret[i]);
            inf['green'] = int(255 - ret[i] / mx[i] * mxg)
            res.append(inf)
        th['subs'] = res
        tab.append(th)
    tab.sort(key=cmp_to_key(comp))
    for i in range(len(tab)):
        if i == 0 or tab[i]['subs'][-1] != tab[i - 1]['subs'][-1]:
            tab[i]['rank'] = i + 1
        else:
            tab[i]['rank'] = tab[i - 1]['rank']
    return render(request, "cms_register/ranking.html",
                  {'users': tab, 'head': head, 'mx': mx, 'exp': expired, 'error': False, 'contest': contest,
                   'un': unof})
