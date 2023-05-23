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

import sys, time
import flask

from fullpy.server.base_rpc import *


class AjaxManager(BaseManager):
  def __init__(self, webapp, session_max_duration, session_max_memory_duration, debug = False):
    super().__init__(webapp, session_max_duration, session_max_memory_duration, debug)
    self.RCP = 0
    
  def destroy_timed_out_sessions(self, exc = None):
    limit = time.time() - self.session_max_memory_duration
    while self.time_ordered_sessions and (limit >= self.time_ordered_sessions[0].session_last_time):
      self.time_ordered_sessions[0].close()
      del self.time_ordered_sessions[0]
      
  def open_session(self, session, session_id, session_token, lang = None):
    new_session, response = BaseManager.open_session(self, session, session_id, session_token, lang)
    if new_session: new_session.on_connected()
    return new_session, response
  
  def close_sessions(self):
    super().close_sessions()
    self.time_ordered_sessions.clear()
    
  def _get_ajax_session(self, session_token):
    session = self.sessions.get(session_token)
    if session:
      try: self.time_ordered_sessions.remove(session)
      except ValueError: pass
      session.session_last_time = time.time()
      TRANS.set_lang((session.user and session.user.webapp_lang) or session.webapp_lang or TRANS.default_lang)
    else:
      if session_token.startswith("@"): session = self.create_session("", session_token, "")
      else:                             session = self.create_session(session_token, "", "")
      if not session: return None
      session.on_connected()
    self.time_ordered_sessions.append(session)
    return session
  
  def route(self, app, path):
    for func_name, func in self.webapp.rpc_funcs.items():
      if self.webapp.has_session:
        if   func is self.webapp.server_new_session_id:
          def wrapper(func = func):
            if self.debug:
              raw_data = flask.request.data.decode("utf8")
              session_token, *data = self.serializer.decode(raw_data)
              print("Message received from %s: %s(%s)" % (session_token, func.__name__[7:], repr(data)[1:-1]), file = sys.stderr)
            return self.serializer.encode(func(None, *data))
          
        else:
          def wrapper(func = func):
            raw_data = flask.request.data.decode("utf8")
            session_token, *data = self.serializer.decode(raw_data)
            if self.debug: print("Message received from %s: %s(%s)" % (session_token, func.__name__[7:], repr(data)[1:-1]), file = sys.stderr)
            
            session = self._get_ajax_session(session_token)
            if session is None:
              if self.debug: print("Invalid session %s: %s(%s)" % (session_token, func.__name__[7:], repr(data)[1:-1]), file = sys.stderr)
              return ""
            
            return self.serializer.encode(func(session, *data))
          
      else:
        def wrapper(func = func):
          raw_data = flask.request.data.decode("utf8")
          data = self.serializer.decode(raw_data)
          if self.debug: print("Message received: %s(%s)" % (func.__name__[7:], repr(data)[1:-1]), file = sys.stderr)
          return self.serializer.encode(func(None, *data))
        
      wrapper.__name__ = func_name
      app.route("%s%s" % (path, func_name[7:]), methods = ["POST"])(wrapper)
      

    if self.webapp.has_session:
      def open_session():
        raw_data = flask.request.data.decode("utf8")
        session_token, *data = self.serializer.decode(raw_data)
        if self.debug: print("Message received from %s: open_session(%s)" % (session_token, repr(data)[1:-1]), file = sys.stderr)
        
        if session_token in self.pending_session_ids: session = None
        else:                                         session = self._get_ajax_session(session_token) # Allow None/failed session here
        new_session, response = self.open_session(session, *data)
        
        if (not response[0]) and ((session_token in self.pending_session_ids) or (session is None)):
          # Initial login failed OR log in failed and not valid session => start unathentified session
          new_session, response = self.open_session(session, "", "", data[2])
          
        return self.serializer.encode(response)
      
      app.route("%sopen_session" % path, methods = ["POST"])(open_session)
