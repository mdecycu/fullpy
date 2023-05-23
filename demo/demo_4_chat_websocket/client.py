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
    self.chat_room = None
    self.messages  = []
    
  def on_session_opened(self, user_login, user_class, client_data):
    if not user_login:
      LoginDialog(None).show_popup()
      return
    
    def done(chat_room_names):
      self.chat_room_names = chat_room_names
      self.select_chat_room(sorted(chat_room_names)[0])
    self.server_get_chat_room_names(done)
    
  def select_chat_room(self, name):
    def done(messages):
      self.chat_room = name
      self.messages  = messages
      self.create_html()
    self.server_join_chat_room(done, name)
    
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
  def client_new_chat_room(self, chat_room_name, chat_room_label):
    webapp.chat_room_names[chat_room_name] = chat_room_label
    webapp.chat_room_list.refresh()
    
  @rpc
  def client_new_message(self, date, user_login, message_text):
    webapp.messages.append((date, user_login, message_text))
    webapp.message_view.add_message(date, user_login, message_text)

    
class ChatRoomList(HTML):
  # def build(self, builder):
  #   def done(chat_room_names):
  #     self << """<div id="chat_room_list"><div class="title">FullPy Chat rooms :</div>"""
  #     for name, label in sorted(chat_room_names.items(), key = lambda i: i[1]):
  #       if name == webapp.chat_room:
  #         self << """<div id="chat_room_%s" class="chat_room selected">%s</div>""" % (name, label)
  #       else:
  #         self << """<div id="chat_room_%s" class="chat_room">%s</div>""" % (name, label)
  #       def on_click(event, name = name):
  #         webapp.select_chat_room(name)
  #       self.bind("chat_room_%s" % name, "click", on_click)
  #     self << """<input id="new_room" type="button" value="Create new room..."></input>"""
  #     self.bind("new_room", "click", self.on_new_room)
  #     self << """</div>"""
  #   webapp.server_get_chat_room_names(done)
    
  def build(self, builder):
    self << """<div id="chat_room_list"><div class="title">FullPy Chat rooms :</div>"""
    for name, label in sorted(webapp.chat_room_names.items(), key = lambda i: i[1]):
      if name == webapp.chat_room:
        self << """<div id="chat_room_%s" class="chat_room selected">%s</div>""" % (name, label)
      else:
        self << """<div id="chat_room_%s" class="chat_room">%s</div>""" % (name, label)
      def on_click(event, name = name):
        webapp.select_chat_room(name)
      self.bind("chat_room_%s" % name, "click", on_click)
    self << """<input id="new_room" type="button" value="Create new room..."></input>"""
    self.bind("new_room", "click", self.on_new_room)
    self << """</div>"""
    
  def on_new_room(self, event): NewRoomDialog().show_popup()
  
  def refresh(self): self.show_replace("chat_room_list")
    

class NewRoomDialog(HTML):
  def build(self, builder):
    self << """<h2>Create new chat room :</h2>"""
    self << """Room label : <input id="chat_room_label" type="text"></input><br/><br/>"""
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
      for date, user_login, message_text in webapp.messages:
        self << self.message_to_html(date, user_login, message_text)
    self << """</div>"""
    
  def message_to_html(self, date, user_login, message_text):
    if user_login == webapp.user_login:
      html = """<div class="message self">"""
    else:
      html = """<div class="message">"""
    html += """<div class="message_header">%s (%s) :</div>""" % (user_login, date)
    html += """<div class="message_content">%s</div></div>""" % message_text
    return html
  
  def add_message(self, date, user_login, message_text):
    document["message_view"].insertAdjacentHTML("beforeend", self.message_to_html(date, user_login, message_text))
    

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
      
      
MyWebApp()
