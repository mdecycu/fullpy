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
from browser import websocket, timer
  

class WebSocketManager(object):
  def __init__(self, webapp, address, session_token, debug = False):
    self.serializer                = webapp.serializer
    self.address                   = address
    self.session_token             = session_token
    self.debug                     = debug
    self._call_id                  = 0
    self._call_id_2_async_callback = {}
    self.groups                    = []
    self.auth_key                  = ""
    self.done_wrappers             = []
    self.opened                    = False
    self.opening                   = False
    self._open_ws()
    
  def server_join_group(self, done, group):
    self.groups.append(group)
    self._server_call(done, "join_group", group)
    
  def server_quit_group(self, done, group):
    self.groups.remove(group)
    self._server_call(done, "quit_group", group)
    
  def _open_ws(self):
    self.ws = websocket.WebSocket(self.address)
    self.ws.bind("message", self.on_ws_message)
    self.ws.bind("close", self.on_ws_close)
    self.ws.bind("error", self.on_ws_error)
    self.ws.bind("open", self.on_ws_open)
    self.opening = True
    
  def on_ws_open(self, e = None):
    self.opened  = True
    self.opening = False
    
  def on_ws_close(self, e = None):
    self.opened = False
    webapp.on_connexion_lost()
    
  def on_ws_error(self, e = None):
    self.opened  = False
    self.opening = False
    
  def on_ws_message(self, e):
    if self.debug: print("Received by websocket:", e.data)
    
    func_name, call_id, data = e.data.split(" ", 2)
    call_id = int(call_id)
    
    if   func_name == "__ok__":
      done = self._call_id_2_async_callback.pop(call_id, None)
      if done:
        try:
          done(self.serializer.decode(data))
        except Exception as e:
          sys.excepthook(*sys.exc_info())
          
    else:
      #func = getattr(webapp, "client_%s" % func_name, None)
      func = webapp.rpc_funcs["client_%s" % func_name]
      if not func: print("No such client func: '%s'" % func_name)
      try:
        response = func(*self.serializer.decode(data))
      except Exception as e:
        sys.excepthook(*sys.exc_info())
        
      if call_id: self.ws.send("__ok__ %s %s" % (call_id, self.serializer.encode(response)))
  
  def _server_call(self, done, func_name, *args, nb_retry = 5):
    if not self.opened:
      if self.opening:
        if nb_retry <= 0: return
        if self.debug: print("Waiting for websocket...")
        def delayed():
          self._server_call(done, func_name, *args, nb_retry = nb_retry - 1)
        timer.set_timeout(delayed, 100)
      else:
        if nb_retry != 5: return
        if self.debug: print("Reopening websocket...")
        self._open_ws()
        previous_session_token = self.session_token
        def delayed():
          def done2(r):
            if self.session_token != previous_session_token: webapp.on_session_lost()
            self._server_call(done, func_name, *args, nb_retry = nb_retry - 1)
          webapp._open_session(done2, self.session_token)
        timer.set_timeout(delayed, 100)
    else:
      if done:
        for wrapper in self.done_wrappers: done = wrapper(done)
        self._call_id += 1
        self._call_id_2_async_callback[self._call_id] = done
        call_id = self._call_id
      else:
        call_id = 0
      self.ws.send("%s %s %s" % (func_name, call_id, self.serializer.encode(list(args))))
    
