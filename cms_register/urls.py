from django.conf.urls import url

from . import views

app_name = 'cms_register'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.loginv, name='login'),
    url(r'^logout/$', views.logoutv, name='logout'),
    url(r'^register/$', views.register, name='register'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^contests/$', views.contest_view, name='contests'),
    url(r'^ranking/(?P<contest_id>[0-9]+)/$', views.ranking, name='ranking'),
    url(r'^unranking/(?P<contest_id>[0-9]+)/$', views.unrank, name='unranking'),
]
