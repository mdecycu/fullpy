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

from fullpy.client import *
from fullpy.client.lang_chooser import LangChooser
from fullpy.util import TRANS

import translation


class MyWebApp(ClientSideWebapp):
  def on_started(self):
    html = HelloHTML()
    html.show()
    
class HelloHTML(HTML):
  def build(self, builder):
    def done(response):
      self << """%s<br/>""" % TRANS["Hello from client"]
      self << """%s<br/>""" % response
      self << """<br/>"""
      self << LangChooser()
    webapp.server_hello(builder.wrap_done(done)) # Call the server_hello() remote function on the server
    

MyWebApp()

