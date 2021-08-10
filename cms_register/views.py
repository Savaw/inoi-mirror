import json
import urllib
from functools import cmp_to_key

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _

from cms_register.utils import password_check, comp, cms_user_exists, \
        cms_add_user, cms_edit_user, cms_add_participation
from cms_register.models import Announcement, Contest, Problem
from cms_register.forms import ProfileForm, UserEditForm, UserForm


def index(request):
    All = Announcement.objects.all()
    return render(request, "cms_register/index.html", {'Announce': All})


def login_view(request):
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
            'last_name': user.last_name,
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


def logout_view(request):
    logout(request)
    return redirect('cms_register:index')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('cms_register:index')
    
    done = False
    cap_error = False
    user_form = UserForm()
    profile_form = ProfileForm()

    if request.method == 'POST':
        cap_error = _check_captcha_error(request)
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if not cap_error and user_form.is_valid() and profile_form.is_valid():            
            user = user_form.save()
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            raw_password = user_form.cleaned_data.get('password1')
            _add_or_edit_cms_user(user, raw_password)

            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            done = True
        
    return render(
        request,
        "cms_register/register.html",
        {
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            'ok': done,
            'caper': cap_error,
            'is_edit': False,
            'user_form': user_form,
            'profile_form': profile_form,
        },
    )


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('cms_register:index')
    
    done = False
    cap_error = False
    user_form = UserEditForm(instance=request.user)
    profile_form = ProfileForm(instance=request.user.profile)

    if request.method == 'POST':
        cap_error = _check_captcha_error(request)
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        
        if not cap_error and user_form.is_valid() and profile_form.is_valid():
            user = User.objects.get(username=request.user.username)
            user.first_name = user_form.cleaned_data.get('first_name')
            user.last_name = user_form.cleaned_data.get('last_name')
            user.email = user_form.cleaned_data.get('email')
        
            raw_password = user_form.cleaned_data.get('password1')
            if raw_password != '':
                user.set_password(raw_password)
            
            user.save()
            profile_form.save(commit=True)

            _add_or_edit_cms_user(user, raw_password)
            done = True
        
    return render(
        request,
        "cms_register/register.html",
        {
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY,
            'ok': done,
            'caper': cap_error,
            'is_edit': True,
            'user_form': user_form,
            'profile_form': profile_form,
        },
    )


def _add_or_edit_cms_user(user, raw_password):
    info = {
        'username':     user.username,
        'email':        user.email,
        'name':         user.first_name,
        'last_name':    user.last_name,
        'password':     raw_password
    }

    not_added = cms_add_user(info)
    if not_added:
        cms_edit_user(info)


def _check_captcha_error(request):
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

        return True
    
    return False


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
    clist = Contest.objects.order_by('-start_time')
    date = dict()
    time = dict()
    durd = dict()
    durt = dict()
    need = dict()
    enterable = dict()
    for contest in clist:
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
            'durd': durd,
            'durt': durt,
            'need': need,
            'timezone': 'UTC',
        },
    )


def problemset_view(request):
    contests = Contest.objects.filter(practice_mode=True) \
        .order_by('-start_time').all()
    problems = list()
    for contest in contests:
        problems.extend(contest.problem_set.all())
    return render(
        request,
        'cms_register/problemset.html',
        {
            'problems': problems,
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


@login_required
def goto_problem_view(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    contest = problem.contest
    if not contest.practice_mode:
        raise Http404('Problem does not exist')
    cms_add_participation(contest.cms_id, request.user.username)
    return redirect(problem.url)
