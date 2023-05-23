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

from browser.session_storage import storage

from fullpy.util import *
from fullpy.client import *


def open_session(done, login, password):
  def done2(session_id):
    webapp._open_session(done, session_id, create_session_token(session_id, login, password))
  session_id = webapp.server_new_session_id(done2)
  
def logout(done): webapp._open_session(done, "")

def _get_stored_token(): return storage.get("%s_session_token" % webapp.name, "")
def _set_stored_token(token): storage["%s_session_token" % webapp.name] = token


class LoginDialog(HTML):
  def __init__(self, done = None, on_error = None):
    HTML.__init__(self)
    self.done = done
    self.on_error = on_error
    
  def build(self, builder):
    self << """<div id="login_box"><h2>%s</h2>
<table>
<tr><td colspan="2" id="login_info"></td></tr>
<tr><td>%s </td><td><input id="login" value=""/></td></tr>
<tr><td>%s </td><td><input id="password" type="password" value=""/><i id="toggle_password"></i></td></tr>
<tr><td colspan="2"><input id="login_button" type="submit" value="%s"/></td></tr>
</table></div>""" % (TRANS["Connection:"], TRANS["Login:"], TRANS["Password:"], TRANS["Ok"])
    
    self.bind("login_button", "click", self.on_login)
    self.bind("login", "keypress", self.on_enter1)
    self.bind("password", "keypress", self.on_enter2)
    self.bind("toggle_password", "click", self.on_toggle)
    
  def on_enter1(self, e):
    if e.key == "Enter":
      e.preventDefault()
      document["password"].focus()
  
  def on_enter2(self, e):
    if e.key == "Enter":
      e.preventDefault()
      self.on_login()
      
  def on_toggle(self, e = None):
    password = document["password"]
    if password.type == "password": password.type = "text"
    else:                           password.type = "password"
  
  @try_debug
  def on_login(self, e = None):
    def done(r):
      if (not r[0]) or (not webapp.session_token.startswith("@")):
        if self.on_error: self.on_error()
        document["login_info"].innerHTML = TRANS["Authentication error, please retry."]
      else:
        hide_popup()
        if self.done: self.done(r)
        
    login = document["login"].value
    if login:
      open_session(done, login, document["password"].value)
    else:
      if self.on_error: self.on_error()
      document["login_info"].innerHTML = TRANS["Authentication error, please retry."]
      
      
