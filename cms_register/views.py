import collections
import json
import re
import subprocess
import urllib
from functools import cmp_to_key

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _

from cms_register.utils import password_check, comp, cms_user_exists, \
        cms_add_user, cms_edit_user, cms_add_participation
from cms_register.models import Announcement, Contest, Participant
from cms_register.forms import ProfileForm


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
    error = dict()
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
            if getInfo(field) is None:
                if not x or field not in ['password', 'password2', 'username']:
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
                ok = False
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
            cap_error = True

        if x:
            profile_form = ProfileForm(
                request.POST,
                instance = request.user.profile,
            )
        else:
            profile_form = ProfileForm(
                request.POST,
            )

        if not profile_form.is_valid():
            ok = False
        if ok and not x:
            user = User.objects.create_user(
                info['username'],
                info['email'],
                info['password'],
            )
            user.first_name = info['name']
            user.last_name = info['lname']
            
            profile = profile_form.save(commit=False)
            profile.user = user

            user.save()
            profile.save()
            not_added = cms_add_user(info)
            if not_added:
                cms_edit_user(info)
            done = True
        if ok and x:
            user = User.objects.get(username=info['username'])
            user.first_name = info['name']
            user.last_name = info['lname']
            user.email = info['email']
            if info['password'] != '':
                user.set_password(info['password'])
            cms_edit_user(info)
            user.save()
            profile_form.save(commit=True)
            done = True
    else:
        if x:
            profile_form = ProfileForm(instance=request.user.profile)
        else:
            profile_form = ProfileForm()
    info['password'] = info['password2'] = ''
    return render(
        request,
        "cms_register/register.html",
        {
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            'ok': done,
            'info': info,
            'error': error,
            'place': place,
            'type': types,
            'caper': cap_error,
            'x': x,
            'profile_form': profile_form,
        },
    )


def format_timedelta(td, type):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours, minutes, seconds = map(int, (days, hours, minutes, seconds))
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
        return '%s Days' % (days)
    if days == 0:
        return '%s Hours' % (hours)
    return '%s Days & %s Hours' % (days, hours)


def contest_view(request):
    done = False
    if request.method == 'POST' and \
            request.user.is_authenticated and \
            request.POST.get('register') == 'register':
        cid = request.POST.get('cid')
        con = Contest.objects.get(id=cid)
        if Participant.objects.filter(user=request.user, contest=con).count() == 0:
            partof = Participant(user=request.user, contest=con)
            partof.save()
            subprocess.call(['cmsAddParticipation', '-c', str(con.cms_id), request.user.username])
            done = True
    clist = Contest.objects.order_by('-start_time')
    date = dict()
    time = dict()
    durd = dict()
    durt = dict()
    need = dict()
    cdown = dict()
    enterable = dict()
    for contest in clist:
        cdown[contest.id] = max(0, int((contest.start_time - timezone.now() + contest.duration).total_seconds()))
        tmp = timezone.localtime(contest.start_time)
        date[contest.id] = tmp.strftime("%d %b %Y")
        time[contest.id] = tmp.strftime("%H:%M")
        cend = tmp + contest.duration
        durd[contest.id] = cend.strftime('%d %b %Y')
        durt[contest.id] = cend.strftime('%H:%M')
        need[contest.id] = format_timedelta(contest.contest_time, 1)

        can_enter = contest.is_enterable(timezone.now())
        can_enter = can_enter and request.user.is_authenticated
        enterable[contest.id] = can_enter

    return render(
        request,
        "cms_register/contests.html",
        {
            'contests': clist,
            'date': date,
            'time': time,
            'enterable': enterable,
            'done': done,
            'durd': durd,
            'durt': durt,
            'need': need,
            'timezone': 'UTC',
        },
    )


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
        th = dict()
        li = user.decode().replace('\n', '').split('\t')
        th['name'] = li[1]
        res = []
        ret = li[2:]
        for i in range(len(ret)):
            inf = dict()
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


@login_required
def goto_contest_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    if not contest.is_enterable(timezone.now()):
        return redirect('cms_register:contests')
    cms_add_participation(contest.cms_id, request.user.username)
    return redirect(contest.url)
