Remote function calls (RPC, remote procedure call)
==================================================

Creating a remotely-callable function
-------------------------------------

In the Webapp class, a remotely-callable function can be defined by using the ``@rpc`` decorator.

Server-side
...........

Remotely-callable functions defined in the server must be prefixed by ``server_``.
Their first argument is always the session object (which is None if there is no session), and additional arguments
are allowed.

Here is an example:

::

  class MyWebApp(ServerSideWebapp):
    def __init__(self):
      [...]
      
    @rpc # Mark the function as remotely callable by the client
    def server_remote_function(self, session, argument1, argument2):
      return argument1 + argument2


Client-side
...........

Remotely-callable functions defined in the client are supported only if you use WebSockets;
they must be prefixed by ``client_``. Contrary to server ones, they have no session argument.

Here is an example:

::

  class MyWebApp(ClientSideWebapp):
    def __init__(self):
      [...]
      
    @rpc # Mark the function as remotely callable by the server
    def client_remote_function(self, argument1, argument2):
      return argument1 + argument2


Calling a remote function
-------------------------

When calling a a remotely-callable function, the first argument is always a callback function
that will be called with the returned value.
You may pass ``None`` as callback if you don't need the returned value.


Client-side
...........

In the client, remotely-callable server functions can be called directly on the webapp.

Here are examples, with and without callback:

::
  
  def done(response):
    print(response)
  webapp.server_remote_function(done, 2, 3)
  
  webapp.server_remote_function(None, 2, 3)


Server-side
...........

In the server, remotely-callable client functions can be called at three levels:

 * **directly on the webapp:** in that case, the function is executed for **all** connected clients.
 * **on a Session object:** in that case, the function is executed for the corresponding client.
 * **on a Group object:** in that case, the function is executed for all clients in that Group.


Here are examples:

::

  def done(response):
    print(response)
  webapp.client_remote_function(done, 2, 3)
  
  session.client_remote_function(done, 2, 3)
  
  group.client_remote_function(done, 2, 3)
  


Serialization and supported datatypes
-------------------------------------

FullPy uses its own object serializer for serializing remote functions arguments and return values.
It supports all basic Python datatypes (including int, float, str, tuple, list and dict)
and can be extended for serializing Python objects and/or OWL ontology entities.
It produce a JSON compatible serialization if the encoded data is JSON compatible;
however, it also supports non-JSON feature, such as Python tuples and dictionaries with non-string keys.

For more information on the serializer, please refer to :doc:`serializer`.


WebSocket example
-----------------


The two next subsections give an example of an Hello World FullPy web application with WebSocket
(the code can be found in the "demo/demo_1_hello_world_websocket" directory of FullPy).
We have already seen a similar ajax example (see :doc:`start`).


Hello World server example
..........................

::
   
  from gevent import monkey
  monkey.patch_all()

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
      self.use_websocket(debug = True)

    @rpc # Mark the function as remotely callable by the client (RPC = remote procedure call)
    def server_hello(self, session): # The name of server-side functions MUST starts with "server_"
      def f():
        gevent.sleep(2.0) # Wait 2 seconds
        session.client_update_speech(None, "Goodbye!") # Call the client_update_speech() remote function on the client
      gevent.spawn(f) # Execute f() in a separate "greenlet" microthread, in parallel
      
      return "Hello world!"

  from fullpy.server.gunicorn_backend import *
  serve_forever([MyWebApp()], "http://127.0.0.1:5000")


Hello World client example
--------------------------

::
 
  from fullpy.client import *
  
  class MyWebApp(ClientSideWebapp):
    def on_started(self, url_params):
      def done(response):
        html = HTML("""FullPy Demo loaded Ok! Server says: '<span id="server_speech">%s</span>'.""" % response)
        html.show()
      webapp.server_hello(done) # Call the server_hello() remote function on the server
      
    @rpc # Mark the function as remotely callable by the server (RPC = remote procedure call)
    def client_update_speech(self, text): # The name of client-side functions MUST starts with "client_"
      html = HTML(text)
      html.show(container = "server_speech") # Update the content of the "server_speech" HTML tag
      
  MyWebApp()

