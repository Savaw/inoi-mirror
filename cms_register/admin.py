from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from ordered_model.admin import OrderedModelAdmin

from cms_register.models import Announcement, Contest, Participant, Profile, \
    Problem


class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'country',
        'date_joined',
        'last_login',
    )

    def country(self, user):
        if user.profile:
            return user.profile.country.name
        return ''


class AnnAdmin(OrderedModelAdmin):
    fieldsets = [
        (None, {'fields': ['announce_text']}),
    ]
    list_display = ('announce_text', 'move_up_down_links')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'country')


class ParLine(admin.TabularInline):
    model = Participant
    classes = ['collapse']
    extra = 0


class ConAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['public_name', 'practice_mode'],
        }),
        ('CMS Config', {
            'classes': ('collapse', 'open'),
            'fields': ['cms_id', 'cms_name'],
        }),
        ('Times', {
            'classes': ('collapse', 'open'),
            'fields': ['start_time', 'duration', 'contest_time'],
        }),
        ('Attached', {
            'classes': ('collapse', 'open'),
            'fields': [
                'ranking_file',
            ],
        }),
    ]
    list_display = (
        'name',
        'start_time',
        'duration',
        'cms_id',
        'reg_count',
    )


class ParAdmin(admin.ModelAdmin):
    list_display = ('user', 'contest')


class ProblemAdmin(admin.ModelAdmin):
    list_display = ('name', 'contest')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Announcement, AnnAdmin)
admin.site.register(Contest, ConAdmin)
admin.site.register(Participant, ParAdmin)
admin.site.register(Problem, ProblemAdmin)
