import os
import httplib
import urllib
import urlparse
import jinja2
import xml2obj

hubs = {'central': 'http://incf-dev.crbs.ucsd.edu/central/atlas', 
        'aba': 'http://incf-dev.crbs.ucsd.edu/aba/atlas', 
        'emap': 'http://incf-dev.crbs.ucsd.edu/emap/atlas', 
        'ucsd': 'http://incf-dev.crbs.ucsd.edu/ucsd/atlas', 
        'whs': 'http://incf-dev.crbs.ucsd.edu/whs/atlas'}

class BaseHubCall:

    def __init__(self, hub):
        self.hub = hub
        return

    def call(self):
        parts = urlparse.urlparse(self.url)
        if parts.scheme == 'http':
            conn = httplib.HTTPConnection(parts.netloc)
        else:
            conn = httplib.HTTPSConnection(parts.netloc)
        if parts.query:
            request_url = '%s?%s' % (parts.path, parts.query)
        else:
            request_url = parts.path
        conn.request('GET', request_url)
        self.response = conn.getresponse()
        self.data = self.response.read()
        conn.close()
        if self.response.status == 200:
            self.obj = xml2obj.xml2obj(self.data)
        else:
            self.obj = None
        return

class GetCapabilities(BaseHubCall):

    def __init__(self, hub):
        BaseHubCall.__init__(self, hub)
        self.ident = 'GetCapabilities'
        params = {'service': 'WPS', 'request': 'GetCapabilities'}
        self.url = '%s?%s' % (hubs[self.hub], urllib.urlencode(params))
        self.call()
        return

class DescribeProcess(BaseHubCall):

    def __init__(self, hub, identifier):
        BaseHubCall.__init__(self, hub)
        self.ident = 'DescribeProcess'
        params = {'service': 'WPS', 
                  'version': '1.0.0', 
                  'request': 'DescribeProcess', 
                  'Identifier': identifier}
        self.url = '%s?%s' % (hubs[self.hub], urllib.urlencode(params))
        self.call()
        return

class HubCall(BaseHubCall):

    def __init__(self, hub, identifier, params):
        BaseHubCall.__init__(self, hub)
        self.ident = identifier
        all_params = params.copy()
        all_params['sevice'] = 'WPS'
        all_params['version'] = '1.0.0'
        all_params['request'] = 'Execute'
        all_params['Identifier'] = identifier
        self.url = '%s?%s' % (hubs[self.hub], urllib.urlencode(all_params))
        self.call()
        return

def render_template(template, render_kwargs):
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    t = env.get_template(template)
    return t.render(**render_kwargs)

class BaseHandler:

    """base class for handler objects"""

    def __init__(self, prefix, environ):
        self.prefix = prefix
        self.environ = environ
        self.hub = None
        self.calls = []
        return

    def run(self):
        raise NotImplementedError()

class IndexHandler(BaseHandler):

    def __init__(self, prefix, environ):
        BaseHandler.__init__(self, prefix, environ)
        self.title = 'Index'
        self.breadcrumbs = [('Index', None)]
        return

    def run(self):
        self.status = '200 OK'
        self.content_type = 'text/html'
        template_vars = {'prefix': self.prefix, 
                         'title': self.title, 
                         'breadcrumbs': self.breadcrumbs, 
                         'calls': self.calls, 
                         'hubs': hubs}
        self.output = render_template('index.tmpl', template_vars)
        return

class HubHandler(BaseHandler):

    def __init__(self, prefix, environ, hub):
        BaseHandler.__init__(self, prefix, environ)
        self.hub = hub
        self.title = 'Hub %s' % self.hub
        self.breadcrumbs = [('Index', '/'), 
                            ('Hub %s' % self.hub, None)]
        return

    def run(self):

        if self.hub not in hubs:
            self.status = '404 Not Found'
            self.content_type = 'text/html'
            template_vars = {'prefix': self.prefix, 
                             'title': self.title, 
                             'breadcrumbs': self.breadcrumbs, 
                             'calls': self.calls, 
                             'hub': self.hub}
            self.output = render_template('hub_not_found.tmpl', template_vars)
            return

        call = GetCapabilities(self.hub)
        self.calls.append((call, 'This request was made to get information about the hub'))

        if call.response.status != 200:
            self.status = '200 OK'
            self.content_type = 'text/html'
            template_vars = {'prefix': self.prefix, 
                             'title': self.title, 
                             'breadcrumbs': self.breadcrumbs, 
                             'calls': self.calls}
            self.output = render_template('hub_error.tmpl', template_vars)
            return

        self.status = '200 OK'
        self.content_type = 'text/html'
        template_vars = {'prefix': self.prefix, 
                         'title': self.title, 
                         'breadcrumbs': self.breadcrumbs, 
                         'calls': self.calls, 
                         'hub': self.hub, 
                         'obj': call.obj}
        self.output = render_template('hub.tmpl', template_vars)
        return

class RequestHandler(BaseHandler):

    def __init__(self, prefix, environ, hub, request):
        BaseHandler.__init__(self, prefix, environ)
        self.hub = hub
        self.request = request
        self.title = 'Hub %s request %s' % (self.request, self.hub)
        self.breadcrumbs = [('Index', '/'), 
                            ('Hub %s' % self.hub, '/%s' % self.hub), 
                            ('Request %s' % self.request, None)]
        return

    def run(self):

        info_call = DescribeProcess(self.hub, self.request)
        self.calls.append((info_call, 'This request was made to get information about the request'))

        if info_call.response.status != 200:
            self.status = '200 OK'
            self.content_type = 'text/html'
            template_vars = {'prefix': self.prefix, 
                             'title': self.title, 
                             'breadcrumbs': self.breadcrumbs, 
                             'calls': self.calls}
            self.output = render_template('request_form_error.tmpl', 
                                          template_vars)
            return

        self.status = '200 OK'
        self.content_type = 'text/html'
        template_vars = {'prefix': self.prefix, 
                         'title': self.title, 
                         'breadcrumbs': self.breadcrumbs, 
                         'calls': self.calls, 
                         'hub': self.hub, 
                         'request': self.request, 
                         'obj': info_call.obj}
        self.output = render_template('request_form.tmpl', template_vars)
        return

class ResultsHandler(BaseHandler):

    def __init__(self, prefix, environ, hub, request, vars):
        BaseHandler.__init__(self, prefix, environ)
        self.hub = hub
        self.request = request
        self.vars = vars
        self.title = 'Hub %s %s results' % (self.request, self.hub)
        req_url = '/%s/%s' % (self.hub, self.request)
        self.breadcrumbs = [('Index', '/'), 
                            ('Hub %s' % self.hub, '/%s' % self.hub), 
                            ('Request %s' % self.request, req_url), 
                            ('Results', None)]
        return

    def run(self):

        info_call = DescribeProcess(self.hub, self.request)
        self.calls.append((info_call, 'This request was made to get information about the request'))

        if info_call.response.status != 200:
            self.status = '200 OK'
            self.content_type = 'text/html'
            template_vars = {'prefix': self.prefix, 
                             'title': self.title, 
                             'breadcrumbs': self.breadcrumbs, 
                             'calls': self.calls}
            self.output = render_template('request_form_error.tmpl', 
                                          template_vars)
            return

        params = {}
        if info_call.obj.ProcessDescription.DataInputs \
           and info_call.obj.ProcessDescription.DataInputs.Input:
            for input in info_call.obj.ProcessDescription.DataInputs.Input:
                ident = input.ows_Identifier
                if ident in self.vars:
                    params[ident] = self.vars[ident][0]
                else:
                    params[ident] = ''

        call = HubCall(self.hub, self.request, params)
        self.calls.append((call, 'This call performed the request'))

        self.status = '200 OK'
        self.content_type = 'text/html'
        template_vars = {'prefix': self.prefix, 
                         'title': self.title, 
                         'breadcrumbs': self.breadcrumbs, 
                         'calls': self.calls, 
                         'hub': self.hub, 
                         'request': self.request, 
                         'data': call.data, 
                         'obj': info_call.obj}
        self.output = render_template('request_result.tmpl', template_vars)
        return

def handle(prefix, environ):

    if environ['PATH_INFO'] == prefix:
        return ('302 Moved Temporarily', 
                'text/plain', 
                '', 
                [('Location', '%s/' % prefix)])
#    elif not environ['PATH_INFO'].startswith(prefix+'/'):
#        return ('500 Internal Server Error', 
#                'text/plain', 
#                'Server error: DAI application handling non-DAI URL', 
#                [])

#    path_parts = environ['PATH_INFO'][len(prefix):].strip('/').split('/')
    path_parts = environ['PATH_INFO'].strip('/').split('/')

    assert len(path_parts) > 0
    hub = path_parts[0]

    if len(path_parts) == 1:

        if hub == '':
            ho = IndexHandler(prefix, environ)
        else:
            ho = HubHandler(prefix, environ, hub)

    else:

        request = path_parts[1]

        try:
            l = int(environ['CONTENT_LENGTH'])
        except:
            ho = RequestHandler(prefix, environ, hub, request)
        else:
            if not l:
                ho = RequestHandler(prefix, environ, hub, request)
            else:
                data = environ['wsgi.input'].read(l)
                vars = urlparse.parse_qs(data)
                if vars['dai-submit'][0] != 'Submit':
                    ho = RequestHandler(prefix, environ, hub, request)
                else:
                    ho = ResultsHandler(prefix, environ, hub, request, vars)

    ho.run()

    return (ho.status, ho.content_type, ho.output, [])

# eof
