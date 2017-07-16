import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from ordered_model.models import OrderedModel


# Create your models here.
class Announcement(OrderedModel):
    def __str__(self):
        return self.announce_text

    announce_text = models.CharField(max_length=2000)

    class Meta(OrderedModel.Meta):
        pass


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "rankings_txt/%s.%s" % (uuid.uuid4(), ext)
    return filename


class Contest(models.Model):
    def __str__(self):
        return self.contest_name

    contest_name = models.CharField(max_length=2000)
    start_time = models.DateTimeField('Start')
    duration = models.DurationField()
    contest_time = models.DurationField(default=timedelta(0))
    cms_id = models.IntegerField(default=0)
    ranking_file = models.FileField(upload_to=get_file_path, blank=True)
    unofficial_ranking_file = models.FileField(upload_to=get_file_path, blank=True)
    contest_url = models.CharField(max_length=2000, default='#')

    def reg_count(self):
        return self.participant_set.count()


class Participant(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Contestant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2000, default='-')
    school = models.CharField(max_length=2000, default='-')
