from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from ordered_model.admin import OrderedModelAdmin

from cms_register.models import Announcement, Contest, Participant, Profile


class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined',
        'last_login',
    )


class AnnAdmin(OrderedModelAdmin):
    fieldsets = [
        (None, {'fields': ['announce_text']}),
    ]
    list_display = ('announce_text', 'move_up_down_links')


class ParLine(admin.TabularInline):
    model = Participant
    classes = ['collapse']
    extra = 0


class ConAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['contest_name', 'cms_id']}),
        ('Times', {
            'classes': ('collapse', 'open'),
            'fields': ['start_time', 'duration', 'contest_time'],
        }),
        ('Attached', {
            'classes': ('collapse', 'open'),
            'fields': [
                'contest_url',
                'ranking_file',
                'unofficial_ranking_file',
            ],
        }),
    ]
    list_display = (
        'contest_name',
        'start_time',
        'duration',
        'cms_id',
        'reg_count',
    )


class ParAdmin(admin.ModelAdmin):
    list_display = ('user', 'contest')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Announcement, AnnAdmin)
admin.site.register(Contest, ConAdmin)
admin.site.register(Participant, ParAdmin)
