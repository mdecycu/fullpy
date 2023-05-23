# FullPy
# Copyright (C) 2022-2023 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# INSERM, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from browser import window, document, alert, timer

from fullpy.util import TRANS
from fullpy.serializer import Serializer

_initial_data = None

def try_debug(f):
  def f2(*args, **kargs):
    try:
      f(*args, **kargs)
    except Exception as e:
      sys.excepthook(*sys.exc_info())
  f2.__name__ = f.__name__
  return f2

def export_to_js(f):
  setattr(window, f.__name__, try_debug(f))
  return f

def delayed(func, delay = 0):
  timer.set_timeout(func, delay)
  return func
  
  

class HTML:
  build = None
  
  def __init__(self, html = ""):
    self._bindings = []
    self._html     = [html] if html else []
    
  def add(self, x):
    self._html.append(x)
    if isinstance(x, HTML): self._bindings.append(x)
    return self
  __lshift__ = __iadd__ = add
  
  def bind(self, html_id, event, func): self._bindings.append((html_id, event, func))
  
  def exec_bindings(self):
    for i in self._bindings:
      if isinstance(i, tuple): document[i[0]].bind(i[1], i[2])
      else: i.exec_bindings()
      
  def _build(self, builder):
    if self.build:
      builder.current_html = self
      self._html     = []
      self._bindings = []
      self.build(builder)
      
    for i in self._html:
      if isinstance(i, HTML): i._build(builder)
      
  def _get_html(self):
    return "".join(i._get_html() if isinstance(i, HTML) else i for i in self._html)
  
  def _call_when_ready(self, done):
    builder = HTMLBuilder(done)
    webapp.rpc_manager.done_wrappers.append(builder.wrap_done)
    self._build(builder)
    webapp.rpc_manager.done_wrappers.remove(builder.wrap_done)
    if builder.nb_async == 0: done()
    return builder
  
  def show(self, container = "main_content"):
    def done():
      document[container].innerHTML = self._get_html()
      self.exec_bindings()
    self._call_when_ready(done)
    if container == "main_content": HTML.current_main_content = self
    
  def show_replace(self, replaced_id):
    def done():
      replaced = document[replaced_id]
      replaced.insertAdjacentHTML("afterend", self._get_html())
      replaced.remove()
      self.exec_bindings()
    self._call_when_ready(done)
    
  def show_popup(self, add_close_button = True, allow_close = True, container = "popup_window"):
    def done():
      html = self._get_html()
      if add_close_button:
        html = """<div id="close_button_%s" class="close_button">X</div>%s""" % (id(self), html)
      html = """<div id="popup_window_content" style="max-height: %spx">%s</div>""" % (0.88 * window.innerHeight, html)
      
      container_tag = document[container]
      container_tag.innerHTML = html
      container_tag.style.display = "block"
      
      def hide(e = None): hide_popup(e, container)
      
      if allow_close:
        def on_escape_popup(e = None):
          if e.key == "Escape":
            e.preventDefault()
            e.stopPropagation()
            hide_popup(e, container)
        document.bind("keyup", on_escape_popup)
        container_tag.bind("click", hide)
        document["popup_window_content"].bind("click", _stop_propagation)
      if add_close_button: document["close_button_%s" % id(self)].bind("click", hide)
      self.exec_bindings()
    self._call_when_ready(done)
    
    
def _stop_propagation(e): e.stopPropagation()

def hide_popup(event = None, container = "popup_window"):
  popup = document[container]
  popup.style.display = "none"
  popup.innerHTML = ""
  document.unbind("keyup")
  
class HTMLBuilder:
  def __init__(self, done):
    self.done     = done
    self.nb_async = 0
    self.nb_done  = 0
    self.current_html = None
    
  def wrap_done(self, done):
    self.nb_async += 1
    def func(r, current_html = self.current_html):
      done(r)
      self.nb_done += 1
      webapp.rpc_manager.done_wrappers.append(self.wrap_done)
      for i in current_html._html:
        if isinstance(i, HTML): i._build(self)
      webapp.rpc_manager.done_wrappers.remove(self.wrap_done)
        
      if self.nb_done == self.nb_async: self.done()
    return func
  
 
def rpc(func):
  ClientSideWebapp._rpc_funcs.append(func)
  return func


 
class _TmpWebapp(object):
  def __init__(self):
    self.serializer = Serializer(None)
    self.rpc        = rpc
    

#__builtins__.webapp = None
__builtins__.webapp = _TmpWebapp()

class ClientSideWebapp(object):
  _rpc_funcs = []
  def __init__(self):
    self.serializer    = webapp.serializer
    __builtins__.webapp = self
    self.modules_proxy = self.serializer.modules_proxy
    self.started       = False
    self.websocket     = None
    self.ajax          = None
    self.rpc_manager   = None
    self.rpc_funcs     = { func.__name__ : getattr(self, func.__name__) for func in ClientSideWebapp._rpc_funcs }
    del ClientSideWebapp._rpc_funcs
    self.session_token = ""
    self.user_login    = ""
    self.user_class    = ""
    
    query = window.location.href.split("?", 1)
    if len(query) == 2:
      query = query[1].split("#", 1)[0]
      query = query.replace("%2B", "+").replace("%20", " ").replace("%25", "%")
      self.url_params = dict(kv.split("=", 1) for kv in query.split("&"))
    else:
      self.url_params = {}
      
    lang = self.url_params.get("lang") or (window.navigator.language or window.navigator.languages[0])
    if lang: TRANS.set_lang(lang[:2])
    
    #self.serializer = Serializer(None)
    
    global _initial_data
    self.initial_data = _initial_data
    if _initial_data: _initial_data = None
    
    for opt in ["fullpy", "serializer", "websocket", "ajax", "session"]:
      if opt in window.WEBAPP_OPTS: getattr(self, "use_%s" % opt)(**dict(window.WEBAPP_OPTS[opt]))
      
    if not "session" in window.WEBAPP_OPTS: self.on_started()
    window.WEBAPP_OPTS = None
    
  def use_fullpy(self, name):
    self.name = name
    
  def use_serializer(self, ignore_none, ignore_empty_list):
    self.serializer.ignore_none       = ignore_none
    self.serializer.ignore_empty_list = ignore_empty_list
    
  def use_session(self, session_id, client_reloadable_session):
    self.reloadable_session = client_reloadable_session
    self.set_session_token(session_id, False)
    
    if client_reloadable_session:
      from fullpy.client.auth import _get_stored_token
      session_token_or_id = _get_stored_token()
      if session_token_or_id:
        if session_token_or_id.startswith("@"): # It's a token
          return self._open_session(None, session_id, session_token_or_id)
        else:
          return self._open_session(None, session_token_or_id, "")
        
    self._open_session(None, session_id)
    
  def _open_session(self, done, session_id = "", session_token = ""):
    def done2(r):
      ok, user_class, client_data, lang, new_session_id = r
      if ok:
        self.set_session_token(new_session_id or session_token or session_id)
        if self.session_token.startswith("@"): self.user_login = self.session_token[1:].split(":", 1)[0]
        else:                                  self.user_login = ""
        self.user_class = user_class
        TRANS.set_lang(lang)
        if not self.started:
          self.started = True
          self.on_started()
        self.on_session_opened(self.user_login, user_class, client_data)
      if done: done(r)
      
    self.server_open_session(done2, session_id, session_token, TRANS.lang)
    
  def set_session_token(self, session_token, store = True):
    self.session_token = self.rpc_manager.session_token = session_token
    if store and self.reloadable_session:
      from fullpy.client.auth import _set_stored_token
      _set_stored_token(session_token)
      
  def use_websocket(self, debug):
    import fullpy.client.websocket
    self.websocket = fullpy.client.websocket.WebSocketManager(self, "ws://%s/_websocket" % window.location.href.split("://", 1)[1].split("?", 1)[0].rsplit("/", 1)[0], self.session_token, debug)
    self.set_rpc_manager(self.websocket)
    
  def use_ajax(self, debug):
    import fullpy.client.ajax
    if "session" in window.WEBAPP_OPTS:
      self.ajax = fullpy.client.ajax.SessionAjaxManager(self, "_ajax/", self.session_token, debug)
    else:
      self.ajax = fullpy.client.ajax.AjaxManager(self, "_ajax/", self.session_token, debug)
    self.set_rpc_manager(self.ajax)
    
  def set_rpc_manager(self, rpc_manager):
    self.rpc_manager = rpc_manager
    self.server_join_group = rpc_manager.server_join_group
    self.server_quit_group = rpc_manager.server_quit_group
    
  def rpc(self, func):
    self.rpc_funcs[func.__name__] = func
    return func
  
  def __getattr__(self, attr):
    if attr.startswith("server_"):
      def specific_server_call(done, *args, func_name = attr[7:]):
        if not ((done is None) or callable(done)): raise ValueError("First argument to remote calls must be the 'done()' callable or None!")
        return self.rpc_manager._server_call(done, func_name, *args)
      setattr(self, attr, specific_server_call)
      return specific_server_call
    raise AttributeError(attr)
  
  def on_started(self): pass
  def on_session_opened(self, user_login, user_class, client_data): pass
  def on_connexion_lost(self): print("Connexion to server lost...")
  def on_session_lost(self): print("Session lost...")
