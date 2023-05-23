FullPy
======

FullPy is a high-level Python module for developing client-server web application. Here are the main features:

 * Both client and server are written in Python, and can share pieces of code.
   FullPy uses `Brython <https://brython.info/>`_ for client-side execution of Python in the web browser.
   
 * Semantic-aware data persistance using OWL ontologies instead of a database.
   FullPy uses `Owlready2 <https://bitbucket.org/jibalamy/owlready2>`_ for managing ontologies and automatically storing them in a SQLite3 database.
 
 * Remote function calls between client and server, with object serialization.
   FullPy can use both Ajax (single way client->server calls) or WebSockets (client->server and server->client calls)

 * FullPy also provides many high-level services, such as authentication, translation support, HTML widget system, etc.

 * FullPy can run over multiple backend: Flask, Werkzeug and Gunicorn (only Gunicorn is supported for WebSockets).

  
Short example
-------------

Here is an example of FullPy web application:

::

  # Server
  
  import sys, os, os.path
  from fullpy.server import *

  class MyWebApp(ServerSideWebapp):
    def __init__(self):
      ServerSideWebapp.__init__(self)
      self.name          = "demo"
      self.url           = "/index.html"
      self.title         = "FullPy demo"
      self.static_folder = os.path.join(os.path.dirname(__file__), "static")

      self.use_python_client(os.path.join(os.path.dirname(__file__), "client.py"))
      self.use_ajax(debug = True)

    @rpc # Mark the function as remotely callable by the client (RPC = remote procedure call)
    def server_hello(self, session):
      return "Hello world!"

  from fullpy.server.gunicorn_backend import *
  serve_forever([MyWebApp()], "http://127.0.0.1:5000")


::

  # Client

  from fullpy.client import *
  
  class MyWebApp(ClientSideWebapp):
    def on_started(self):
      def done(response):
        html = HTML("""FullPy Demo loaded Ok! Server says: '%s'.""" % response)
        html.show()
      webapp.server_hello(done) # Call the server_hello() remote function on the server

  MyWebApp()

  
Changelog
---------

version 1 - 0.1
***************

* Initial release

    
Links
-----

FullPy on BitBucket (Git development repository): https://bitbucket.org/jibalamy/fullpy

FullPy on PyPI (Python Package Index, stable release): https://pypi.python.org/pypi/FullPy

Documentation: http://fullpy.readthedocs.io/


Contact "Jiba" Jean-Baptiste Lamy:

::

  <jean-baptiste.lamy *@* univ-paris13 *.* fr>
  LIMICS
  INSERM, Université Sorbonne Paris Nord, Sorbonne Université
  Bureau 149
  74 rue Marcel Cachin
  93017 BOBIGNY
  FRANCE
