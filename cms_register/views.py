#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import collections
import json
import locale
import re
import subprocess
import urllib
from functools import cmp_to_key

import jdatetime
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaulttags import register
from django.utils import timezone
from django.utils.translation import gettext as _ 

from cms_register.utils import password_check, persian_num, comp, cms_user_exists, cms_add_user, cms_edit_user
from .models import Announcement, Contest, Participant


# Create your views here.


def index(request):
    All = Announcement.objects.all()
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
    if user is not None or request.user.is_authenticated:
        login(request, user)
        user_info = {
            'username': user.username,
            'name': user.first_name,
            'lname': user.last_name,
            'password': passw,
            'email': user.email,
        }
        if not cms_user_exists(user.username):
            cms_add_user(user_info)
        else:
            cms_edit_user(user_info)
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

    if request.user.is_authenticated and not x:
        return redirect('cms_register:index')
    if not request.user.is_authenticated and x:
        return redirect('cms_register:index')
    fields = ['username', 'email', 'password', 'password2', 'name', 'lname']
    place = {'username': _("username"),
             'email': _("email"),
             'password': _("password"),
             'password2': _("password repeat"),
             'name': _("name"),
             'lname': _("family name"),
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
                    addError(field, _("this field is mandatory"))
            else:
                info[field] = getInfo(field)
        if x:
            info['username'] = request.user.username
        if len(info['username']) > 150:
            addError('username', _("most 150 chars"))
        if not re.match("^[A-Za-z0-9_-]+$", info['username']):
            addError('username', _("only num latin underline"))
        if not x and User.objects.filter(username=info['username']).exists():
            addError('username', _("duplicate username"))
        if not re.match(r"[^@]+@[^@]+\.[^@]+", info['email']):
            addError('email', _("invalid email"))
        if info['password'] != '' or info['password2'] != '':
            passdet = password_check(info['password'])
            if passdet['length_error']:
                addError('password', _("at least 8 char"))
            if passdet['digit_error']:
                addError('password', _("at least 1 num"))
            if passdet['lowercase_error'] and passdet['uppercase_error']:
                addError('password', _("at least 1 latin"))
            if info['password'] != info['password2']:
                addError('password2', _("password dont match"))
        if not re.match(r"^[a-zA-Z ]+$", info['name']):
            addError('name', _("name must english"))
        if not re.match(r"^[a-zA-Z ]+$", info['lname']):
            addError('lname', _("family must english"))
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
            user.save()
            #not_added = cms_add_user(info)
            #if not_added:
            #    cms_edit_user(info)
            done = True
        if ok and x:
            user = User.objects.get(username=info['username'])
            user.first_name = info['name']
            user.last_name = info['lname']
            user.email = info['email']
            if info['password'] != '':
                user.set_password(info['password'])
#                subprocess.call(
#                    ['python', 'scripts/cmsEditUser.py', '-p', info['password'], '-e', info['email'], '-fn',
#                     info['name'],
#                     '-ln', info['lname'], info['username']])
#            else:
#                subprocess.call(
#                    ['python', 'scripts/cmsEditUser.py', '-e', info['email'], '-fn', info['name'], '-ln', info['lname'],
#                     info['username']])
            user.save()
            done = True
    info['password'] = info['password2'] = ''
    return render(request, "cms_register/register.html",
                  {'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY, 'ok': done, 'info': info, 'error': error,
                   'place': place, 'type': types, 'caper': cap_error, 'x': x})


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
    if request.method == 'POST' and request.user.is_authenticated and request.POST.get('register') == 'register':
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
        if request.user.is_authenticated and contest.participant_set.filter(user=request.user).count() > 0:
            registered[contest.id] = True
    return render(request, "cms_register/contests.html",
                  {'contests': clist, 'date': date, 'time': time, 'expired': expired, 'registered': registered,
                   'done': done, 'dur': dur, 'need': need, 'ended': ended, 'cdown': cdown})


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
    head[0] = '#'
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
            inf['score'] = int(ret[i])
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
