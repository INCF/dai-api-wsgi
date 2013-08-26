import traceback
import wsgiref.simple_server
import handler

# this is the base of this webapp; URLs will be '%s/stuff' % prefix
# so prefix shouldn't end in '/'
prefix = '/dai-api'

def handle(environ):
    reload(handler)
    return handler.handle(prefix, environ)

def application(environ, start_response):
 
    if environ['PATH_INFO'] == '%s/dai.css' % prefix:
        data = open('dai.css').read()
        response_headers = [('Content-Type', 'text/css'), 
                            ('Content-Length', str(len(data)))]
        start_response('200 OK', response_headers)
        return [data]

    try:
        (status, content_type, output, handler_headers) = handle(environ)
    except Exception, data:
        status ='500 Internal Server Error'
        content_type = 'text/plain'
        output = 'Error!\n\n'
        output += traceback.format_exc()
        handler_headers = []

    output = output.encode('UTF-8')

    response_headers = [('Content-Type', content_type), 
                        ('Content-Length', str(len(output)))]
    response_headers.extend(handler_headers)
    start_response(status, response_headers)

    return [output]

if __name__ == '__main__':
    httpd = wsgiref.simple_server.make_server('', 8000, application)
    print 'Serving on port 8000...'
    httpd.serve_forever()

# eof
