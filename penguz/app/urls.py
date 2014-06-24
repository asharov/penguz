from django.conf.urls import patterns, include, url

urlpatterns = patterns('app.views',
    url(r'^$', 'index'),
    url(r'^register$', 'register'),
    url(r'^own$', 'own'),
    url(r'^help$', 'help'),
    url(r'^profile$', 'profile'),
    url(r'^editprofile$', 'editprofile'),
    url(r'^contest/(?P<contest_id>\d+)/', 'contest'),
    url(r'^start/(?P<contest_id>\d+)/', 'start'),
    url(r'^results/(?P<contest_id>\d+)/', 'results'),
    url(r'^answer/(?P<contest_id>\d+)/', 'answer'),
    url(r'^create$', 'create'),
    url(r'^addpuzzles/(?P<contest_id>\d+)/', 'addpuzzles'),
    url(r'^edit/(?P<contest_id>\d+)/', 'edit'),
    url(r'^editpuzzles/(?P<contest_id>\d+)/', 'editpuzzles'),
)

urlpatterns += patterns('',
    url(r'^logout/?$', 'django.contrib.auth.views.logout', { 'next_page': '/' }),
    url(r'', include('django.contrib.auth.urls')),
)
