Client application
==================

The client application should import fullpy.client, subclass fullpy.server.ClientSideWebapp,
and create an instance of the subclass, as in the following example:

::
  
   from fullpy.client import *
   
   class MyWebApp(ClientSideWebapp):
     def on_started(self):
       html = HTML("""FullPy Demo loaded Ok!""")
       html.show()
       
   MyWebApp()

The web application object can be accessed anywhere with the ``webapp`` global built-in variable.

  
ClientSideWebapp instances have the following attributes:
   
   * ``url_params``: a dictionary with the parameters found in the query part of the URL.
   
   * ``initial_data``: the initial data sent by the server (if any).

     
ClientSideWebapp has the following methods that can be reimplemented:

.. method:: on_started()

   Called once, when the web app starts.

.. method:: on_session_opened(user_login, user_class, client_data)
   
   Called when a session is opened, and after on_started().
   Notice that it is **also** called for anonymous sessions (in that case, ``user_login`` is empty).

   * ``user_login``: the login of the user.
   * ``user_class``: the name of the class of the user (as a string; usefull if you define several subclasses of User).
   * ``client_data``: the additional client data sent by the server (if any).
     
.. method:: on_connexion_lost()

   Called when the connexion to the server is lost.

   
.. method:: on_session_lost()

   Called when the session is lost (e.g. it has expired).
   
