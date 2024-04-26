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
from browser import ajax


class AjaxManager(object):
  def __init__(self, webapp, address, session_token, debug = False):
    self.serializer      = webapp.serializer
    self.address         = address
    self.session_token   = session_token
    self.debug           = debug
    self.groups          = []
    self.auth_key        = ""
    self.done_wrappers   = []
    
  def server_join_group(self, done, group):
    self.groups.append(group)
    self._server_call(done, "join_group", group)
    
  def server_quit_group(self, done, group):
    self.groups.remove(group)
    self._server_call(done, "quit_group", group)
    
  def _server_call(self, done, func_name, *args):
    if done is None:
      return ajax.post("%s%s" % (self.address, func_name), headers = { "Content-Type": "text/plain" }, data = self.serializer.encode(list(args)))
    else:
      for wrapper in self.done_wrappers: done = wrapper(done)
      def oncomplete(req):
        try: done(self.serializer.decode(req.text))
        except Exception as e: sys.excepthook(*sys.exc_info())
      return ajax.post("%s%s" % (self.address, func_name), headers = { "Content-Type": "text/plain" }, data = self.serializer.encode(list(args)), oncomplete = oncomplete)
    
    
class SessionAjaxManager(AjaxManager):
  def _server_call(self, done, func_name, *args):
    def oncomplete(req):
      try:
        if req.text == "":
          webapp.on_session_lost()
          def done2(session_id):
            self._server_call(done, func_name, *args)
          webapp._open_session(done2)
          
        elif done:
          done(self.serializer.decode(req.text))
          
      except Exception as e:
        sys.excepthook(*sys.exc_info())

    return ajax.post("%s%s" % (self.address, func_name), headers = { "Content-Type": "text/plain" }, data = self.serializer.encode([self.session_token, *args]), oncomplete = oncomplete)
  
