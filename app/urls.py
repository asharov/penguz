from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('app.views',
    url(r'^$', 'index'),
    url(r'^register$', 'register'),
    url(r'^contest/(?P<contest_id>\d+)/', 'contest'),
    url(r'^start/(?P<contest_id>\d+)/', 'start'),
    url(r'^results/(?P<contest_id>\d+)/', 'results'),
    url(r'^answer/(?P<contest_id>\d+)/', 'answer'),
    url(r'^create/$', 'create'),
    url(r'^addpuzzles/(?P<contest_id>\d+)/', 'addpuzzles'),
    url(r'^edit/(?P<contest_id>\d+)/', 'edit'),
    url(r'^editpuzzles/(?P<contest_id>\d+)/', 'editpuzzles'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^login$', 'login'),
    url(r'^logout$', 'logout', { 'next_page': '/' }),
)
