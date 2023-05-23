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


class MyWebApp(ClientSideWebapp):
  def on_started(self):
    def done(response):
      html = HTML("""FullPy Demo loaded Ok! Server says: '<span id="server_speech">%s</span>'.""" % response)
      html.show()
    webapp.server_hello(done) # Call the server_hello() remote function on the server
    
  @rpc # Mark the function as remotely callable by the server (RPC = remote procedure call)
  def client_update_speech(self, text): # The name of client-side functions MUST starts with "client_"
    html = HTML(text)
    html.show(container = "server_speech") # Update the content of the "server_speech" HTML tag
    
MyWebApp()

