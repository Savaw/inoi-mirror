import re
import subprocess
import json
import os.path

from django.template.defaulttags import register
from django.conf import settings


ADD_USER_EXEC = os.path.join(
    settings.CMS_BINARIES_DIR,
    'cmsAddUser',
)
ADD_PARTICIPATION_EXEC = os.path.join(
    settings.CMS_BINARIES_DIR,
    'cmsAddParticipation',
)


class CmsProblemData:
    @staticmethod
    def from_dict(data):
        inst = CmsProblemData()
        inst.name = data['name']
        inst.title = data['title']
        return inst


class CmsContestData:
    @staticmethod
    def from_dict(data):
        inst = CmsContestData()
        inst.name = data.get('name', '')
        inst.participants = data.get('participants', 0)
        inst.problems = list()
        for pdata in data['tasks']:
            inst.problems.append(CmsProblemData.from_dict(pdata))
        return inst


def cms_user_exists(username):
    if not settings.CMS_AVAILABLE:
        return False
    result = subprocess.run([
        settings.CMS_PYTHON,
        './scripts/cmsHasUser.py',
        username,
        ], stdout=subprocess.PIPE).stdout
    result = bool(int(result.decode("utf-8").split('\n')[-2]))
    return result


def cms_add_user(info):
    if not settings.CMS_AVAILABLE:
        return False
    print("adding")
    print(info)
    return subprocess.call([
        ADD_USER_EXEC,
        '-p', info['password'],
        '-e', info['email'],
        info['name'],
        info['lname'],
        info['username'],
    ])


def cms_add_participation(cid, username):
    if not settings.CMS_AVAILABLE:
        return False
    subprocess.call([
        ADD_PARTICIPATION_EXEC,
        '-c',
        f'{cid}',
        username,
    ])
    return True


def cms_edit_user(info):
    if not settings.CMS_AVAILABLE:
        return False
    print("editing")
    print(info)
    args = [
            settings.CMS_PYTHON,
            './scripts/cmsEditUser.py',
            '-e', info['email'],
            '-fn', info['name'],
            '-ln', info['lname'],
            ]
    if info.get('password'):
        args.extend(['-p', info['password']])
    args.append(info['username'])
    return subprocess.call(args)


def cms_get_contest_data(cid):
    if not settings.CMS_AVAILABLE:
        return None
    args = [
        settings.CMS_PYTHON,
        './scripts/cmsGetContest.py',
        f'{cid}',
    ]
    output = subprocess.run(args, stdout=subprocess.PIPE).stdout
    output = output.decode('utf-8')
    jdata = output.split('\n')[1]
    data = json.loads(jdata)
    if data.get('success'):
        return CmsContestData.from_dict(data)
    return None


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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


l2p = [u'۰', u'۱', u'۲', u'۳', u'۴', u'۵', u'۶', u'۷', u'۸', u'۹']


def persian_num(value):
    if isinstance(value, int):
        value = str(value)
    for i in range(10):
        value = value.replace(str(i), l2p[i])
    return value


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

