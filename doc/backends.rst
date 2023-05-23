Backends
========

FullPy supports several backend servers.

Gunicorn backend
----------------

The Gunicorn backend supports **both** Ajax and WebSockets web apps.
Ajax web apps can be run with or without GEvent.
WebSockets web apps automatically use Gevent.

::
   
   from fullpy.server.gunicorn_backend import *
   serve_forever([MyWebApp()], "http://127.0.0.1:5000", url_prefix = "", flask_app = None, log_file = None, nb_process = 1, max_nb_websockect = 5000, worker_class = None, use_gevent = False, gunicorn_options = None)


Werkzeug backend
----------------

The Werkzeug backend supports only Ajax web apps.

::
   
   from fullpy.server.werkzeug_backend import *
   serve_forever([MyWebApp()], "http://127.0.0.1:5000", url_prefix = "", flask_app = None, log_file = None, nb_process = 1, werkzeug_options = None)


Flask backend
-------------

The Flask backend supports only Ajax web apps.

It is not exactely a backend: it just create a Flask application for the web app (or add the web app to an existent Flask
application). Then, it is up to you to choose any Flask-compatible server (i.e. any WSGI server).

::
   
   from fullpy.server.werkzeug_backend import *
   flask_app = serve_forever([MyWebApp()], "http://127.0.0.1:5000", url_prefix = "", flask_app = None)
