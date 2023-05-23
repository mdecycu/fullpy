Starting a new project with FullPy
==================================

Directory architecture
----------------------

To start a new project, follow these simple steps:

 * Create a directory for your project

 * Create a "static" subdirectory in that directory

 * Copy the following files in the "static" subdirectory:
   
   * "fullpy.css" (from fullpy/static)

   * "brython.js" and "brython_stdlib.js" (from `Brython <https://github.com/brython-dev/brython/releases>`_)

 * Create a "server.py" and "client.py" Python scripts in your project directory

That's all! You should obtain the following hierarchy:

* project_directory/
   * static/
      - brython.js
      - brython_stdlib.js
      - fullpy.css
   * client.py
   * server.py

     
The two next subsections give an example of an Hello World FullPy web application
(the code can be found in the "demo/demo_1_hello_world_ajax" directory of FullPy).


Hello World server example
--------------------------

::
  
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


Hello World client example
--------------------------

::

  from fullpy.client import *
  
  class MyWebApp(ClientSideWebapp):
    def on_started(self):
      def done(response):
        html = HTML("""FullPy Demo loaded Ok! Server says: '%s'.""" % response)
        html.show()
      webapp.server_hello(done) # Call the server_hello() remote function on the server

  MyWebApp()


Running the web application
---------------------------

To run your web application, simply execute the server.py Python script.

FullPy will automatically compile the client part of the web application into Javascript, if needed.

::

   python3 ./server.py

Then, open the following address in your web browser: http://127.0.0.1:5000/demo/index.html
