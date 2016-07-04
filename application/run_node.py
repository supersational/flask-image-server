from application import app
if 1:
    # this seems to be the simplest method:
    import subprocess
    import datetime
    # @app.before_first_request
    # def before_first_request():
    #     print '########### Restarted, first request @ {} ############'.format(datetime.datetime.utcnow())
    #     subprocess.Popen(['node', 'application/server.js', app.config['NODE_SECRET_KEY']], shell=True)

else:
    # this has a race condition, but could be useful for querying the server in future
    import os
    import socket
    import urllib2
    import threading
    import psutil    
    import os

    def is_node_running():
        print "checking"
        # print psutil.()
        if 'node.exe' in [x for x in dir(psutil) if 'list' in x]:
            print 'found node.exe'
            return True
        # timeout in seconds
        timeout = 1
        socket.setdefaulttimeout(timeout)

        # this call to urllib2.urlopen now uses the default timeout
        # we have set in the socket module
        req = urllib2.Request('http://localhost:5001/alive')
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError:
            print "urllib2.URLError"
            return False
        response = response.read()
        print 'http://localhost:5001/alive response:', str(response)
        if response!='alive':
            print "response not alive"
            return False
        return True

    def run_node_server_if_not_already_running():
        if not is_node_running():
            server = None
            try:
                server = subprocess.Popen(['node', 'server.js'], shell=True)
            except WindowsError:
                print os.environ['COMSPEC']
                subprocess.call('dir', shell=True)


    def run_node_server():
        t = threading.Timer(0, run_node_server_if_not_already_running)
        t.start()

if __name__=='__main__':
    print "opening node"
    run_node_server()