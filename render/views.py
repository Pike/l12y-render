import json
import mimetypes
import os
import os.path

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse

def index(request):
    pages = []
    for dir, dirs, files in os.walk(settings.DOM_BASE_DIR):
        for file in files:
            base, ext = os.path.splitext(file)
            print ext
            if ext == '.pagedata':
                rel = os.path.relpath(dir, settings.DOM_BASE_DIR)
                rel = rel.split(os.path.pathsep)
                pages.append('/'.join(rel) + '/' + base)
    return render(request, 'render/index.html', {
                    'pages': pages,
                  })

def page(request, path):
    path += '.pagedata'
    segs = path.split('/')
    app = segs[0]
    filepath = os.path.join(settings.DOM_BASE_DIR, *segs)
    pagedata = json.load(open(filepath))
    return render(request, 'render/page.html', {
                  'head': pagedata['head'],
                  'body': pagedata['body'],
                  'app': app
                  })

def static(request, app, path):
    fullpath = os.path.join(settings.GAIA_BUILD_DIR, app, *(path.split('/')))
    content_type, encoding = mimetypes.guess_type(fullpath)
    content_type = content_type or 'application/octet-stream'
    response = StreamingHttpResponse(open(fullpath, 'rb'),
                                     content_type=content_type)
    return response
