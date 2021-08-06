import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from ordered_model.models import OrderedModel
from django_countries.fields import CountryField
from django.utils.translation import gettext as _
from django.conf import settings


class Announcement(OrderedModel):
    def __str__(self):
        return self.announce_text

    announce_text = models.TextField()

    class Meta(OrderedModel.Meta):
        pass


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "rankings_txt/%s.%s" % (uuid.uuid4(), ext)
    return filename


class Contest(models.Model):
    def __str__(self):
        return self.name

    public_name = models.CharField(max_length=400, blank=True, null=False)
    cms_name = models.CharField(max_length=200, blank=True, null=False)
    start_time = models.DateTimeField('Start')
    duration = models.DurationField()
    contest_time = models.DurationField(default=timedelta(0))
    cms_id = models.IntegerField(default=0)
    ranking_file = models.FileField(upload_to=get_file_path, blank=True)
    practice_mode = models.BooleanField(default=False)
    participants_count = models.IntegerField(default=0)

    @property
    def name(self):
        return self.public_name or self.cms_name

    @property
    def url(self):
        if self.cms_name:
            return settings.CWS_ADDRESS + '/' + self.cms_name
        else:
            return '#'

    def is_enterable(self, time):
        started = time >= self.start_time
        ended = time > self.start_time + self.duration
        is_official = started and not ended
        cms_exists = settings.CMS_AVAILABLE and self.cms_name
        can_enter = is_official or self.practice_mode
        return can_enter and cms_exists


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = CountryField(blank_label=_('(select country)'))


class Problem(models.Model):
    cms_name = models.CharField(max_length=100, blank=False, null=False)
    public_name = models.CharField(max_length=200, blank=True, null=False)
    contest = models.ForeignKey(Contest, null=False, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.public_name or self.cms_name

    @property
    def url(self):
        return self.contest.url + '/tasks/' + self.cms_name + '/description'
