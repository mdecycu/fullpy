HTML widget system
==================

Creating HTML pieces
--------------------

In the client, the HTML class can be used for creating and displaying pieces of HTML, and widgets.

A simple, fixed, piece of HTML code can be created as follows:

::

   html = HTML("""<div>This is a <b>piece</b> of HTML</div>""")
   
   
It can also be created over several lines, as follows:

::

   html = HTML()
   html << """<div>First part</div>"""
   html << """<div>Second part</div>"""
   html << """<div id="part3">Third part</div>"""
   

The bind() method can be used to bind function to Javascript events.


.. method:: bind(html_id, event, func)
   
   Bind a callback function to an event, for the given HTML id.
   Notice that the actual binding may not occur immediately, but when the HTML piece will be displayed in the web browser.
   For more information on the available events and the ``func`` argument, please refer to `Brython documentation <https://brython.info/static_doc/en/events.html>`_.
   
   * ``html_id``: the ID the HTML element.
   * ``event``: The name of the event.
   * ``func``: a callable that will be called when the event occur.

Here is an example:

::

   def on_click(event):
     print("CLICKED!")
     
   html.bind("part3", click, on_click)



Creating HTML widgets
---------------------

Finally, you can subclass HTML to create your own widget.

Here is an example:
   
::

   class MyWidget(HTML):
     def build(self, builder):
       self << """<div>First part</div>"""
       self << """<div>Second part</div>"""
       self << """<input id="ok_%s" type="button" value="Ok"></input>""" % id(self)
       self.bind("ok_%s" % id(self), "click", self.on_ok)
    
     def on_ok(self, event):
       print("OK clicked")


HTML widgets, i.e. subclasses of HTML, can also be inserted inside HTML pieces (including other widgets). For example:

::

   html = HTML()
   html << """<div>Plain HTML</div>"""
   html << MyWidget()
   
   
Displaying an HTML piece
------------------------

The following methods of HTML objects can be used to display a HTML piece:

.. method:: show(container = "main_content")
   
   Show the piece of HTML in the web browser.
   
   * ``container``: the HTML ID of the element that will display the HTML piece.
     By default, it is displayed in the entire HTML page.


.. method:: show_replace(replaced_id)
   
   Show the piece of HTML in the web browser, replacing the element of the given ID.
   
   * ``replaced_id``: the HTML ID of the element that will replaced by the HTML piece.


.. method:: show_popup(add_close_button = True, allow_close = True, container = "popup_window")
   
   Show the piece of HTML in the web browser, in a popup window.
   
   * ``add_close_button``: if True, add a close button "X" at the top-right of the popup window.
   
   * ``allow_close``: if True, the popup window is closed when the user click outside the window or press escape.
   
   * ``container``: the HTML ID of the node that will used to display the popup window.
     

Finally, ``hide_popup()`` can be used to close the popup window.

.. method:: hide_popup(event = None, container = "popup_window")
   
   Hide the current popup window.
   
   * ``event``: No-op argument (only present in order to allow the use of hide_popup() as a callback to Javascript events).
   
   * ``container``: the HTML ID of the node that is used to display the popup window.
     


   
Refreshing an HTML piece
------------------------

A common trick is to use show_replace() for refreshing an HTML widget, as in the following example:

::

   class MyRefreshableWidget(HTML):
     def build(self, builder):
       self << """<div id="widget_%s">""" % id(self)
       self << """... [add content of the widget here]"""
       self << """</div>"
       
     def refresh(self):
       self.show_refresh("widget_%s" % id(self))

