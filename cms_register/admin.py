from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from .models import Announcement, Contest, Participant


# Register your models here.

class AnnAdmin(OrderedModelAdmin):
    fieldsets = [
        (None, {'fields': ['announce_text']}),
    ]
    list_display = ('announce_text', 'move_up_down_links')


admin.site.register(Announcement, AnnAdmin)


class ParLine(admin.TabularInline):
    model = Participant
    classes = ['collapse']
    extra = 0


class ConAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['contest_name', 'cms_id']}),
        ('Times', {'classes': ('collapse', 'open'), 'fields': ['start_time', 'duration', 'contest_time']}),
        ('Attached',
         {'classes': ('collapse', 'open'), 'fields': ['contest_url', 'ranking_file', 'unofficial_ranking_file']}),
    ]
    list_display = ('contest_name', 'start_time', 'duration', 'cms_id', 'reg_count')
    # inlines = [ParLine]


admin.site.register(Contest, ConAdmin)


class ParAdmin(admin.ModelAdmin):
    list_display = ('user', 'contest')


admin.site.register(Participant, ParAdmin)
