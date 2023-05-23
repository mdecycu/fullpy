Welcome to FullPy's documentation!
**********************************

FullPy is a high-level Python module for developping client-server web application. Here are the main features:

 * **Both client and server are written in Python**, and can share pieces of code.
   FullPy uses `Brython <https://brython.info/>`_ for client-side execution of Python in the web browser.
   
 * **Semantic-aware data persistance using OWL ontologies** instead of a database.
   FullPy uses `Owlready2 <https://bitbucket.org/jibalamy/owlready2>`_ for managing ontologies and automatically storing them in a SQLite3 database.
 
 * **Remote function calls** between client and server, with object serialization.
   FullPy can use both Ajax (single way client->server calls) or WebSockets (client->server and server->client calls)

 * FullPy also provides many high-level services, such as authentication, translation support, HTML widget system, etc.

 * FullPy can run over multiple backend: Flask, Werkzeug and Gunicorn (only Gunicorn is supported for WebSockets).


Table of content
----------------

.. toctree::
   install.rst
   start.rst
   server.rst
   client.rst
   backends.rst
   rpc.rst
   html.rst
   translations.rst
   onto.rst
   session.rst
   group.rst
   serializer.rst
   demos.rst
   contact.rst
