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
from fullpy.client.auth import *


class MyWebApp(ClientSideWebapp):
  def __init__(self):
    ClientSideWebapp.__init__(self)
    self.chat_rooms = {}
    self.chat_room  = None
    self.messages   = []
    
  def on_session_opened(self, user_login, user_class, client_data):
    if not user_login:
      LoginDialog(None).show_popup()
      return
    
    def done(chat_rooms):
      self.chat_rooms = { chat_room.name : chat_room for chat_room in chat_rooms }
      self.select_chat_room(self.chat_rooms[ sorted(self.chat_rooms)[0] ])
    self.server_get_chat_rooms(done)
    
  def select_chat_room(self, chat_room):
    self.chat_room = chat_room
    def done(messages):
      self.messages = messages
      self.create_html()
    self.server_join_chat_room(done, chat_room)
    print("JOIN", chat_room)
    
  def create_html(self):
    self.chat_room_list = ChatRoomList()
    self.message_view   = MessageView()
    self.entry_box      = EntryBox()
    
    self.main_html = HTML()
    self.main_html << """<table id="chat_table" cellspacing="0"><tr><td>"""
    self.main_html << self.chat_room_list
    self.main_html << """</td><td>"""
    self.main_html << self.message_view
    self.main_html << self.entry_box
    self.main_html << """</td></tr></table>"""
    self.main_html.show()
    
  @rpc
  def client_new_chat_room(self, chat_room):
    webapp.chat_rooms[chat_room.name] = chat_room
    webapp.chat_room_list.refresh()
    
  @rpc
  def client_new_message(self, message):
    webapp.messages.append(message)
    webapp.message_view.add_message(message)
    
class ChatRoomList(HTML):
  def build(self, builder):
    self << """<div id="chat_room_list"><div class="title">FullPy Chat rooms:</div>"""
    for chat_room in sorted(webapp.chat_rooms.values(), key = lambda i: i.label):
      if chat_room is webapp.chat_room:
        self << """<div id="chat_room_%s" class="chat_room selected">%s</div>""" % (chat_room.name, chat_room.label)
      else:
        self << """<div id="chat_room_%s" class="chat_room">%s</div>""" % (chat_room.name, chat_room.label)
      def on_click(event, chat_room = chat_room):
        webapp.select_chat_room(chat_room)
      self.bind("chat_room_%s" % chat_room.name, "click", on_click)
    self << """<input id="new_room" type="button" value="Create new room..."></input>"""
    self.bind("new_room", "click", self.on_new_room)
    self << """</div>"""
    
  def on_new_room(self, event): NewRoomDialog().show_popup()
  
  def refresh(self): self.show_replace("chat_room_list")
  

class NewRoomDialog(HTML):
  def build(self, builder):
    self << """<h2>Create new chat room:</h2>"""
    self << """Room label: <input id="chat_room_label" type="text"></input><br/><br/>"""
    self << """<input id="ok" type="button" value="Ok"></input>"""
    self.bind("ok", "click", self.on_ok)
    
  def on_ok(self, event):
    chat_room_label = document["chat_room_label"].value.strip()
    webapp.server_create_chat_room(None, chat_room_label)
    hide_popup()
    
    
class MessageView(HTML):
  def build(self, builder):
    self << """<div id="message_view">"""
    if webapp.messages:
      for message in webapp.messages:
        self << self.message_to_html(message)
    self << """</div>"""
    
  def message_to_html(self, message):
    if message.author.login == webapp.user_login:
      html = """<div class="message self">"""
    else:
      html = """<div class="message">"""
    html += """<div class="message_header">%s (%s/%s/%s %s:%s):</div>""" % (message.author.login, message.date.day, message.date.month, message.date.year, message.date.hour, message.date.minute)
    html += """<div class="message_content">%s</div></div>""" % message.text
    return html
  
  def add_message(self, message):
    document["message_view"].insertAdjacentHTML("beforeend", self.message_to_html(message))
    

class EntryBox(HTML):
  def build(self, builder):
    self << """<div id="entry_box">"""
    self << """<table id="entry_table"><tr><td>Say&nbsp;something:</td>"""
    self << """<td id="entry_td"><input id="entry" type="text"></input></td>"""
    self << """<td><input id="send" type="button" value="Send"></input></td></tr></table>"""
    self << """</div>"""
    self.bind("entry", "keypress", self.on_keypress)
    self.bind("send",  "click",    self.on_send)
    
  def on_keypress(self, event):
    if event.key == "Enter": self.on_send(event)
    
  def on_send(self, event):
    text = document["entry"].value.strip()
    if text:
      webapp.server_add_message(None, text)
      document["entry"].value = ""
      
MyWebApp()
