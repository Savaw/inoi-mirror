import json
from datetime import datetime, timedelta
from urllib.request import urlopen

from django.shortcuts import render, redirect

from .models import Username


def index(request):
    if not request.user.is_staff:
        return redirect("cms_register:index")
    member = []
    tm = datetime.now() - timedelta(days=7)
    base = "http://codeforces.com/api/user.status?handle="
    count_par = "&count="
    from_par = "&from="
    for someone in Username.objects.all():
        user = someone.handle
        solved = {}
        url = base + user
        response = urlopen(url);
        data = json.loads(response.read().decode())
        status = data['result']
        bad = False;
        for submition in status:
            if datetime.fromtimestamp(submition['creationTimeSeconds']) > tm:
                if submition['verdict'] == "OK":
                    solved[str(submition['problem']['contestId']) + submition['problem']['index']] = submition[
                        'creationTimeSeconds']
        member.append({'name': user, 'solved': len(solved)})
    starttime = tm.strftime("%A %d. %B %Y %H:%M")
    print(starttime)
    return render(request, "scoreboard/index.html", {'mems': member, 'from': starttime})
