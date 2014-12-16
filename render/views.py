import json
import mimetypes
import os
import os.path

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from django.views.generic import View

import git

mimetypes.add_type('text/plain', '.properties')

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
    app = segs[1]
    filepath = os.path.join(settings.DOM_BASE_DIR, *segs)
    pagedata = json.load(open(filepath))
    # find and replace the theme app css
    for headmatter in pagedata['head']:
        headmatter['type_'] = headmatter['_type']
        if headmatter['_type'] == 'style':
            if headmatter['href'].startswith('app://theme'):
                href = headmatter['href']
                href = href.split('theme.gaiamobile.org', 1)[1]
                headmatter['href'] = href
    return render(request, 'render/page.html', {
                  'head': pagedata['head'],
                  'body': pagedata['body'],
                  'app': app
                  })

def screenshot(request, revision, path):
    imgpath = path + '.en-US.png'
    innerpath = path + '-inner.en-US.png'
    repo = git.Repo(settings.DOM_BASE_DIR)
    commit = repo.commit(revision)
    tree = commit.tree
    imgsha = tree[imgpath].hexsha
    try:
        innersha = tree[innerpath].hexsha
    except KeyError:
        innersha = None
    try:
        parent = commit.parents[0]
    except IndexError:
        parent = None
    priorsha = priorinner = None
    if parent:
        diffs = tree.diff(parent, paths=[imgpath, innerpath])
        for diff in diffs:
            if diff.new_file or diff.deleted_file:
                continue
            if diff.b_blob.path == imgpath:
                priorsha = diff.b_blob.hexsha
            if diff.b_blob.path == innerpath:
                priorinner = diff.b_blob.hexsha
    return render(request, 'render/screenshot.html', {
                  'image': imgsha,
                  'inner': innersha,
                  'prior': priorsha,
                  'priorinner': priorinner,
                  })


class ImageView(View):
    def __init__(self, *args, **kwargs):
        self.queue = []
        View.__init__(self, *args, **kwargs)

    def get(self, request, sha):
        repo = git.Repo(settings.DOM_BASE_DIR)
        blob = git.Blob.new(repo, sha)
        blob.stream_data(self)
        content_type, encoding = mimetypes.guess_type('foo.png')
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(''.join(self.queue),
                                content_type=content_type)
        return response

    def write(self, data):
        self.queue.append(data)

image = ImageView.as_view()

def static(request, app, path):
    fullpath = os.path.join(settings.GAIA_BUILD_DIR, app, *(path.split('/')))
    content_type, encoding = mimetypes.guess_type(fullpath)
    content_type = content_type or 'application/octet-stream'
    response = StreamingHttpResponse(open(fullpath, 'rb'),
                                     content_type=content_type)
    return response

def l10n(request, app, path):
    if 'shared/locales/branding/' in path:
        # use official branding, and hardcode en-US.
        realpath = path.rsplit('.', 2)[0] + '.en-US.properties'
        realpath = realpath.replace('/branding/', '/branding/official/')
        return static(request, app, realpath)
    if '.en-US.' in path:
        # load orig en-US files from build_stage
        return static(request, app, path)
    # munge path to work against hg
    path = path.replace('locales/', '/')
    base, loc, ext = path.rsplit('.', 2)
    path = base + '.' + ext
    if not path.startswith('/shared/'):
        realpath = '/apps/' + app + '/' + path
    else:
        realpath = path
    fullpath = os.path.join(settings.LOCALE_BASEDIR, loc, *(realpath.split('/')))
    response = StreamingHttpResponse(open(fullpath, 'rb'),
                                     content_type='text/plain; charset=utf-8')
    return response
