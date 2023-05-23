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

from gevent import monkey
monkey.patch_all()

import sys, os, os.path, datetime, gevent
from owlready2 import *
from fullpy.server import *


world       = World(filename = "/tmp/demo_chat.sqlite3")
fullpy_onto = get_fullpy_onto(world)
chat_onto   = world.get_ontology("http://test.org/chat.owl")

with chat_onto:
  class MyUser(fullpy_onto.User): pass
    
  class MySession(fullpy_onto.Session):
    def on_connected(self, previous_session = None):
      print("New user connected: %s" % self.user)
      
  class ChatRoom(fullpy_onto.Group): pass
  
  class Message(Thing):
    def as_tuple(self):
      return ("%s/%s/%s %s:%s" % (self.date.day, self.date.month, self.date.year,
                                  self.date.hour, self.date.minute), self.user.login, self.text)
    
  class text(Message >> str, FunctionalProperty): pass
  class date(Message >> datetime.datetime, FunctionalProperty): pass
  class messages(ChatRoom >> Message): pass
  
  chat_onto.MyUser("user1", login = "user1", password = "123")
  chat_onto.MyUser("user2", login = "user2", password = "123")
  chat_onto.MyUser("user3", login = "user3", password = "123")
  
  chat_onto.ChatRoom("bike_room", label = ["Bike riding"])
  chat_onto.ChatRoom("bird_room", label = ["Bird watching"])
  chat_onto.ChatRoom("prog_room", label = ["Python programming"])
  
  
class MyWebApp(ServerSideWebapp):
  def __init__(self):
    ServerSideWebapp.__init__(self)
    self.name          = "demo_4"
    self.title         = "FullPy demo"
    self.url           = "/index.html"
    self.static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
    self.js            = []
    self.css           = ["demo_4.css"]
    
    self.use_python_client(os.path.join(os.path.dirname(__file__), "client.py"))
    self.use_ontology_quadstore(world)
    self.use_session(chat_onto.MySession, chat_onto.ChatRoom)
    self.use_websocket(debug = True)
    
  @rpc
  def server_get_chat_room_names(self, session):
    return { chat_room.name : chat_room.label.first() for chat_room in ChatRoom.instances() }
  
  @rpc
  def server_join_chat_room(self, session, chat_room_name):
    if session.groups: session.quit_group(session.groups[0])
    chat_room = chat_onto[chat_room_name]
    session.join_group(chat_room)
    return [message.as_tuple() for message in sorted(chat_room.messages, key = lambda message: message.date)]
  
  @rpc
  def server_create_chat_room(self, session, chat_room_label):
    with chat_onto:
      chat_room = chat_onto.ChatRoom(label = chat_room_label)
    self.client_new_chat_room(None, chat_room.name, chat_room_label)
    
  @rpc
  def server_add_message(self, session, text):
    chat_room = session.groups[0]
    with chat_onto:
      message = chat_onto.Message(date = datetime.datetime.now(), user = session.user, text = text)
      chat_room.messages.append(message)
    chat_room.client_new_message(None, *message.as_tuple())
    
    
from fullpy.server.gunicorn_backend import *
serve_forever([MyWebApp()], "http://127.0.0.1:5000")

# You can now open the following URL in your browser: http://127.0.0.1:5000/demo_4/index.html
