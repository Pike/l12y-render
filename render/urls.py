from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^_page/(.*)', 'render.views.page'),
    url(r'^_screenshot/(.*?)/(.*)', 'render.views.screenshot'),
    url(r'^_image/(.*)', 'render.views.image'),
    url(r'^_static/([^/]+)/(.+)', 'render.views.static'),
    url(r'^$', 'render.views.index'),
)
