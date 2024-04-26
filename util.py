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

__all__ = ["int_2_base_62", "create_session_token", "Translator", "TRANS"]

import sys, hashlib

_BASE_62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
def int_2_base_62(n):
  if n == 0: return [0]
  digits = []
  while n:
    digits.append(_BASE_62[n % 62])
    n //= 62
  return "".join(digits[::-1])

def create_session_token(session_id, login, password):
  return "@%s:%s" % (login, int_2_base_62(int(hashlib.sha256((session_id + password).encode("utf8")).hexdigest(), 16)))


class Translator(object):
  def __init__(self, **args):
    self._lang = self._default_lang = "en"
    self.dicts = args
    if not "en" in self.dicts: self.dicts["en"] = {}
    self._current_dict = self._default_dict = self.dicts["en"]
    
  def set_lang(self, lang):
    self._lang = lang
    if lang in self.dicts: self._current_dict = self.dicts[lang]
    else:                  self._current_dict = self.dicts[lang] = {}
    
  def get_lang(self): return self._lang
  lang = property(get_lang, set_lang)
  
  def set_default_lang(self, lang):
    self._default_lang = lang
    self._default_dict = self.dicts.get(lang) or {}
  def get_default_lang(self): return self._default_lang
  default_lang = property(get_default_lang, set_default_lang)
  
  def add_translations(self, lang, d):
    if lang in self.dicts: self.dicts[lang].update(d)
    else:                  self.dicts[lang] = d
    
  def __getitem__(self, key):
    return self._current_dict.get(key) or self._default_dict.get(key, key)

  def format(self, a, b):
    s = a % b
    r = self._current_dict.get(s)
    if r: return r
    ra = self._current_dict.get(a)
    rb = self._current_dict.get(b, b)
    if ra and rb: return ra % rb
    return self._default_dict.get(s) or self._default_dict.get(a, a) % self._default_dict.get(b, b)
  
  
  if sys.platform == "brython":
    def get_lang_first(self, l, lang):
      if lang.endswith("_any"):
        shorter = lang[:-4]
        for x in L:
          if isinstance(x, locstr) and ((x.lang == shorter) or x.lang.startswith("%s_" % shorter) or x.lang.startswith("%s-" % shorter)): return str(x)
      elif len(lang) > 3:
        lang  = lang.casefold()
        lang2 = lang.replace("_", "-").casefold()
        for x in l:
          if isinstance(x, locstr) and ((x.lang.casefold() == lang) or (x.lang.casefold() == lang2)): return str(x)
      else:
        for x in l:
          if isinstance(x, locstr) and (x.lang == lang): return str(x)
      return ""
    
    def from_entity(self, e):
      labels = getattr(e, "label", [])
      return self.get_lang_first(labels, self._lang) or self.get_lang_first(labels, self._default_lang) or e.name.replace("_", " ")
    
    def from_annotation(self, annot):
      return self.get_lang_first(annot, self._lang) or self.get_lang_first(annot, self._default_lang) or (annot[0] if annot else "")
    
  else:
    def from_entity(self, e):
      return e.label.get_lang_first(self._lang) or e.label.get_lang_first(self._default_lang) or e.name.replace("_", " ")
    
    def from_annotation(self, annot):
      return annot.get_lang_first(self._lang) or annot.get_lang_first(self._default_lang) or annot.first() or ""
    
  
  def dict_from_annotation(self, annot):
    return { getattr(i, "lang", "") : str(i) for i in annot }
  
  def from_dict(self, d):
    return d.get(self._lang) or d.get(self._default_lang) or d.get("", "")
  
TRANS = Translator()
