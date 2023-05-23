Server application
==================

The server application should import fullpy.server, subclass fullpy.server.ServerSideWebapp,
create an instance of the subclass and pass it to server_forever(), as in the following example:

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
      self.js            = []
      self.css           = []
      self.favicon       = "icon.png"
      
      self.use_python_client(os.path.join(os.path.dirname(__file__), "client.py"))
      self.use_ajax(debug = True)
      
  from fullpy.server.gunicorn_backend import *
  serve_forever([MyWebApp()], "http://127.0.0.1:5000")

In the subclass of ServerSideWebapp, you need to reimplement __init__(). Your __init__() should call the super
implementation, then define some properties and finally call some use_XXX() methods.

The following properties are available:

* ``name`` (mandatory): the name of the web app.
  
* ``url`` (mandatory): the URL of the web app page. The full URL with be the concatenation of the server address,
  the name property and the url property (in the example above, "http://127.0.0.1:5000/demo/index.html").

* ``title`` (mandatory): the title of the web app (showed in the web browser's window titlebar).

* ``static_folder`` (mandatory): the local directory where static files are stored.

* ``js`` (optional): a list of additional Javascript files used by the client.
  Notice that FullPy automatically adds Brython Javascript files as needed.
  Javascript files are expected to be found in the static directory.

* ``css`` (optional): a list of CSS files used by the client.
  Notice that FullPy automatically adds "fullpy.css".
  CSS files are expected to be found in the static directory.

* ``favicon`` (optional): the "favicon" image file, showed in the web browser.
  The favicon is expected to be found in the static directory.

  
use_XXX() methods are used to enable various features of FullPy.
The following use_XXX() methods are available:

.. method:: use_python_client(client_file, force_brython_compilation = False, minify_python_code = False)

  Use a Brython-compiled Python client. The client is automatically compiled to Javascript as needed.

  * ``client_file``: the path to the client Python script (e.g. client.py).
  * ``force_brython_compilation``: if True, compile the client even if its sources have not been modified.
  * ``minify_python_code``: if True, minify the Python source using the "python_minifier" module.
  

.. method:: use_ontology_quadstore(world = None)

  Use an Owlready2 quadstore for persistent data and semantics.

  * ``world``: the Owlready2 World to use (if None, owlread2.default_world is used).
  
  
.. method:: use_session(session_class = None, group_class = None, auth = True, client_reloadable_session = True, session_max_duration = 3888000.0, session_max_memory_duration = 1296000.0)
  
  Use sessions. A **session** is an object available on the server application, and created for each connected client.
  If a given client calls several remote functions on the server, each call will be associated with the same session.
  It thus allows storing client-specific information on the server-side.
  
  FullPy support both **anonymous sessions** (automatically created by the client)
  and **authentified sessions** (with login and password).
  However, the use of authentified sessions requires an ontology quadstore, for storing users and their logins and passwords.
  
  In addition, FullPy support both **in-memory sessions** (lost when the server is stopped and restarted)
  and **persistent sessions** (stored in the ontology quadstore).
  The use of persistent sessions requires an ontology quadstore.
  
  * ``session_class``: the Session class to use. If None, use the default, in-memory, Session class.
    You can provide your own Session class, to reimplement some methods, store additional per-session data,
    and/or create a persistent Session.
  
  * ``group_class``:  the Group class to use. If None, use the default, in-memory, Group class.
    You can provide your own Group class, to reimplement some methods, store additional per-group data,
    and/or create a persistent Group.
  
  * ``auth``: if True, support authentified sessions (which requires an ontology quadstore).

  * ``client_reloadable_session``: if True, allows the client to reload and reuse the previous session.

  * ``session_max_duration``: after that duration (in seconds), sessions are closed and destroyed.
    Default value corresponds to 45 days.
    
  * ``session_max_memory_duration``: after that duration (in seconds), sessions are removed from the memory
    (but still kept in the ontology quadstore, if persistent sessions are used).
    Default value corresponds to 15 days.
    

.. method:: use_ajax(debug = False)
  
  Use Ajax, allowing client->server remote function calls.
  On the contrary, the server cannot call remote functions on the client with Ajax.
  
  * ``debug``: if True, debugging information is written in the console each time a remote function is called.
  
  
.. method:: use_websocket(debug = False)
  
  Use WebSocket, allowing both client->server and server->client remote function calls.
  WebSockets require the use of sessions (anonymous or authentified).
  
  * ``debug``: if True, debugging information is written in the console each time a remote function is called
    (for both the client and the server).
  

The following combination of use_XXX() methods are allowed:

* **use_python_client(); use_ajax():**

  Simple Ajax-based web application, without sessions nor data persistance.
  
  
* **use_python_client(); use_ontology_quadstore(); use_ajax():**

  Ajax-based web application, with data persistance but without sessions.
  Can be used e.g. for a dynamic website based on an ontology.
  
  
* **use_python_client(); use_session(auth = False); use_ajax():**

  Ajax-based web application, with anonymous sessions but without data persistance.
  Anonymous sessions can be used e.g. for keeping user preferences (such as language) during navigation,
  but the preferences will be lost when the user closes the web browser.

  
* **use_python_client(); use_ontology_quadstore(); use_session(); use_ajax():**

  Ajax-based web application, with both sessions and data persistance.
  Sessions can be anonymous or authentified.
  
  
* **use_python_client(); use_session(auth = False); use_websocket():**
  
  WebSocket-based web application, with anonymous sessions but without data persistance.
  
* **use_python_client(); use_ontology_quadstore(); use_session(); use_websocket():**

  WebSocket-based web application, with both sessions and data persistance.
  Sessions can be anonymous or authentified.

Additionnally, when using WebSocket, you need to enable GEvent and to use the Gunicorn backend, as in the following example:

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
      
  from fullpy.server.gunicorn_backend import *
  serve_forever([MyWebApp()], "http://127.0.0.1:5000")



Finally, ClientSideWebapp has the following methods that can be reimplemented:

.. method:: get_initial_data(url_params)
   
   Create the initial data sent to the client.
   By default, no initial data is sent, but you can override this method to send some initial data.
   Initial data will be incorporated in the HTML webpage.
   They will be encoded with repr()
   (NB FullPy **do not** use the serializer to encode initial data, so as you may send a dictionary, and then
   decode its content one piece at a time, when needed).
   
   * ``url_params``: a dictionary with the parameters found in the query part of the URL.

