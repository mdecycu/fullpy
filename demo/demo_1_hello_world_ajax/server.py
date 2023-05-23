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

import sys, os, os.path
from fullpy.server import *


class MyWebApp(ServerSideWebapp):
  def __init__(self):
    ServerSideWebapp.__init__(self)
    self.name          = "demo_1"
    self.url           = "/index.html"
    self.title         = "FullPy demo"
    self.static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
    self.js            = []
    self.css           = []
    
    self.use_python_client(os.path.join(os.path.dirname(__file__), "client.py"))
    self.use_ajax(debug = True)
    
  @rpc # Mark the function as remotely callable by the client (RPC = remote procedure call)
  def server_hello(self, session): # The name of server-side functions MUST starts with "server_"
    return "Hello world!"
    

from fullpy.server.gunicorn_backend import *
serve_forever([MyWebApp()], "http://127.0.0.1:5000")

# You can now open the following URL in your browser: http://127.0.0.1:5000/demo_1/index.html
