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

from fullpy.util import TRANS
from fullpy.client import *

class LangChooser(HTML):
  def build(self, builder):
    self << """<div id="lang_chooser">%s <select id="lang_chooser_select">""" % TRANS["Language:"]
    for lang in TRANS.dicts:
      self << """<option value="%s"%s>%s</option>""" % (lang, ' selected="1"' if lang == TRANS.lang else "", TRANS["Language '%s'" % lang])
    self << """</select></div>"""
    
    self.bind("lang_chooser_select", "change", self.on_changed)
    
  def on_changed(self, e = None):
    lang = document["lang_chooser_select"].value
    TRANS.set_lang(lang)
    if webapp.session_token:
      def done(response):
        HTML.current_main_content.show()
      webapp.server_set_lang(done, lang)
    else:
      HTML.current_main_content.show()
