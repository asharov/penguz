from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('app.views',
    url(r'^$', 'index'),
    url(r'^contest/(?P<contest_id>\d+)/', 'contest'),
    url(r'^start/(?P<contest_id>\d+)$', 'start'),
    url(r'^password/(?P<contest_id>\d+)$', 'password'),
    url(r'^results/(?P<contest_id>\d+)/', 'results'),
)