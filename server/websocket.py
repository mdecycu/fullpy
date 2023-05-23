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
import gevent, gevent.timeout

from fullpy.server.base_rpc import *

  
class BaseWebSocketManager(BaseManager):
  def __init__(self, webapp, session_max_duration, session_max_memory_duration, debug = False):
    super().__init__(webapp, session_max_duration, session_max_memory_duration, debug)
    self._call_id                  = 0
    self._call_id_2_async_callback = {}
    

class GUnicornWebSocketManager(BaseWebSocketManager):
  def loop(self, ws0):
    try:
      with gevent.Timeout(self.session_max_memory_duration): message = ws0.receive()
    except gevent.timeout.Timeout: return

    func_name, call_id, data = message.split(" ", 2)
    session_id, session_token, lang = self.serializer.decode(data)
    if self.debug: print("First message received from %s: %s(%s)" % (session_id, func_name, repr(data)[1:-1]), file = sys.stderr)
    
    session, response = self.open_session(None, session_id, session_token, lang)
    if not response[0]: session, response = self.open_session(None, "", "", lang)
    ws0.send("__ok__ %s %s" % (call_id, self.serializer.encode(response)))
    
    session._ws = ws0
    
    try:
      session.on_connected()
      
      while True:
        with gevent.Timeout(self.session_max_memory_duration): message = ws0.receive()
        if message is None: break
        if message == "":  continue
        
        func_name, call_id, data = message.split(" ", 2)
        data = self.serializer.decode(data)
        if self.debug: print("Message received from %s: %s(%s)" % (session.session_id or session.session_token, func_name, repr(data)[1:-1]), file = sys.stderr)
        call_id = int(call_id)
        
        if func_name == "__ok__":
          done = self._call_id_2_async_callback.pop(call_id, None)
          if done: done(session, data)
          
        else:
          if func_name == "open_session":
            new_session, response = self.open_session(session, *data)
            if response[0]:
              del session._ws
              session = new_session
              session._ws = ws0
              session.on_connected()
          else:
            response = self.webapp.rpc_funcs["server_%s" % func_name](session, *data)
            
          if call_id: ws0.send("__ok__ %s %s" % (call_id, self.serializer.encode(response)))
          
        session.session_last_time = time.time()
        
    except gevent.timeout.Timeout: pass
    finally:
      session.close()
      try: session._ws.close()
      except WebSocketError: pass
      
  def _client_call(self, session_or_group, done, func_name, *args):
    if not ((done is None) or callable(done)): raise ValueError("First argument to remote calls must be the 'done()' callable or None!")
    
    from geventwebsocket.exceptions import WebSocketError
    
    if   isinstance(session_or_group, (list, set)): sessions = session_or_group
    elif session_or_group is None:                  sessions = list(self.sessions.values())
    else:                                           sessions = [session_or_group]
    args = self.serializer.encode(list(args))
    
    for session in sessions:
      if done:
        self._call_id += 1
        self._call_id_2_async_callback[self._call_id] = done
        call_id = self._call_id
      else:
        call_id = 0
      try:
        session._ws.send("%s %s %s" % (func_name, call_id, args))
        #if self.debug: print("Message sent to %s: '%s %s %s'" % (session.session_id or session.session_token, func_name, call_id, args), file = sys.stderr)
      except WebSocketError:
        session.close()
        try: session._ws.close()
        except WebSocketError: pass
    
  def route(self, app, path):
    middleware = _APP_2_MIDDLEWARE.get(app)
    if not middleware: middleware = _APP_2_MIDDLEWARE[app] = app.wsgi_app = GUnicornWebSocketMiddleware(app.wsgi_app)
    middleware.ws_routes[path] = self
    
    
_APP_2_MIDDLEWARE = {}
class GUnicornWebSocketMiddleware(object):
  def __init__(self, wsgi_app):
    self.wsgi_app  = wsgi_app
    self.ws_routes = {}
    
  def __call__(self, environ, start_response):
    if "wsgi.websocket" in environ:
      self.ws_routes[environ["PATH_INFO"]].loop(environ["wsgi.websocket"])
      return []
    else:
      return self.wsgi_app(environ, start_response)
    
