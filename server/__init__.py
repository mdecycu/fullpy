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

import sys, os, os.path, flask

from fullpy.util import TRANS
from fullpy.serializer import Serializer


def _gevent_patch_translator():
  from fullpy.util  import Translator
  from gevent.local import local
  
  l = local()
  
  def __init__(self, **args):
    self.default_lang = "en"
    self.dicts = args
    if not "en" in self.dicts: self.dicts["en"] = {}
    self._default_dict = self.dicts["en"]
    
  def set_lang(self, lang):
    l.lang = lang
    l.current_dict = self.dicts.get(lang) or {}
    
  def get_lang(self): return l.lang
  
  def __getitem__(self, key):
    return l.current_dict.get(key) or self._default_dict.get(key, key)
  
  def from_entity(self, e):
    return e.label.get_lang(l.lang).first() or e.label.get_lang(self._default_lang).first() or e.name
  
  def from_annotation(self, annot):
    return annot.get_lang(l.lang).first() or annot.get_lang(self._default_lang).first()
  
  Translator.__init__        = __init__
  Translator.set_lang        = set_lang
  Translator.get_lang        = get_lang
  Translator.lang            = property(get_lang, set_lang)
  Translator.__getitem__     = __getitem__
  Translator.from_entity     = from_entity
  Translator.from_annotation = from_annotation
  
def rpc(func):
  func.__rpc__ = True
  return func

def get_fullpy_onto(world):
  if "http://www.lesfleursdunormal.fr/static/_downloads/fullpy.owl#" in world.ontologies:
    return world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/fullpy.owl").load()
  else:
    return world.get_ontology(os.path.join(os.path.dirname(__file__), "fullpy.owl")).load()
  

class ServerSideWebapp(object):
  def __init__(self):
    self.name                        = ""
    self.title                       = ""
    self.url                         = "/index.html"
    self.static_folder               = "./static"
    self.js                          = []
    self.css                         = []
    self.favicon                     = None
    self.rpc_funcs                   = {}
    self.world                       = None
    self.has_python_client           = False
    #self.has_serializer              = False
    self.has_websocket               = False
    self.has_ajax                    = False
    self.rpc_manager                 = None
    self.has_session                 = False
    self.has_auth                    = False
    self.session_class               = None
    self.group_class                 = None
    self.client_reloadable_session   = False
    self.session_max_duration        = 3888000.0
    self.session_max_memory_duration = 1296000.0
    self._html_index1                = None
    self._html_index2                = None
    self.serializer                  = Serializer(None)
    
    for attr in dir(self.__class__):
      if attr.startswith("server_"):
        func = getattr(self, attr)
        if getattr(func.__func__, "__rpc__", False) == True:
          self.rpc_funcs[func.__name__] = func
      
  def set_external_static_folder(self, static_folder, static_url_path):
    self.static_folder = static_folder
    self.blueprint.static_url_path = static_url_path
    
  def use_python_client(self, client_file, force_brython_compilation = False, minify_python_code = False):
    self.has_python_client = True
    self.client_file       = client_file
    self.client_module     = os.path.splitext(os.path.basename(client_file))[0]
    path = os.path.dirname(client_file)
    while os.path.exists(os.path.join(path, "__init__.py")):
      path, module = path.rsplit(os.sep, 1)
      self.client_module = "%s.%s" % (module, self.client_module)
    self.force_brython_compilation = force_brython_compilation
    self.minify_python_code = minify_python_code
    self.js.append("brython.js")
    self.js.append("%s_brython_modules.js" % self.name)
    self.css.append("fullpy.css")
    
    self.blueprint = flask.Blueprint(self.name, __name__, static_folder = self.static_folder)
    self.blueprint.route(self.url, methods = ["GET"])(self.html_index)
    if self.url.endswith("/index.html"):
      self.blueprint.route(self.url[:-10], methods = ["GET"])(self.html_index)
      
  #def use_serializer(self, ignore_none = False, ignore_empty_list = False):
  #  self.has_serializer = True
  #  self.serializer.ignore_none       = ignore_none
  #  self.serializer.ignore_empty_list = ignore_empty_list
  #  self.serializer.set_world(self.world)
  
  def use_ontology_quadstore(self, world = None):
    #if self.has_serializer: raise ValueError("Please call use_serializer() after use_ontology_quadstore().")
    
    import owlready2
    self.world = world or owlready2.default_world
    self.serializer.set_world(self.world)
    
    if "http://www.lesfleursdunormal.fr/static/_downloads/fullpy.owl#" in self.world.ontologies:
      self.fullpy_onto = self.world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/fullpy.owl").load()
    else:
      self.fullpy_onto = self.world.get_ontology(os.path.join(os.path.dirname(__file__), "fullpy.owl")).load()
      
    from fullpy.server.base_rpc import Session as BaseSession, Group as BaseGroup
    with self.fullpy_onto:
      class Session(owlready2.Thing):
        def __getattr__(self, attr):
          if attr.startswith("client_"): return BaseSession.__getattr__(self, attr)
          return owlready2.Thing.__getattr__(self, attr)
        
        __repr__        = BaseSession.__repr__
        init            = BaseSession.init
        on_init         = BaseSession.on_init
        set_manager     = BaseSession.set_manager
        on_connected    = BaseSession.on_connected
        get_client_data = BaseSession.get_client_data
        #on_group_joined = BaseSession.on_group_joined
        #on_group_quited = BaseSession.on_group_quited
        on_closed       = BaseSession.on_closed
        close           = BaseSession.close
        on_destroyed    = BaseSession.on_destroyed
        destroy         = BaseSession.destroy
        join_group      = BaseSession.join_group
        quit_group      = BaseSession.quit_group
        
      class Group(owlready2.Thing):
        def __getattr__(self, attr):
          if attr.startswith("client_"): return BaseGroup.__getattr__(self, attr)
          return owlready2.Thing.__getattr__(self, attr)
        
        __repr__        = BaseGroup.__repr__
        set_manager     = BaseGroup.set_manager
        destroy         = BaseGroup.destroy
        on_empty        = BaseGroup.on_empty
        
        
  def use_session(self, session_class = None, group_class = None, auth = True, client_reloadable_session = True, session_max_duration = 3888000.0, session_max_memory_duration = 1296000.0):
    if auth and (not self.world): raise ValueError("Need ontology_quadstore for auth! Please call use_ontology_quadstore() before.")
    from fullpy.server.base_rpc import Session, Group
    
    self.has_session                 = True
    self.session_class               = session_class or Session
    self.group_class                 = group_class or Group
    self.has_auth                    = auth
    self.client_reloadable_session   = client_reloadable_session
    self.session_max_duration        = session_max_duration
    self.session_max_memory_duration = session_max_memory_duration
    self.persistent_session          = hasattr(self.session_class, "storid")
    
    self.rpc(self.server_set_lang)
    
  def use_websocket(self, debug = False):
    from fullpy.server.websocket import GUnicornWebSocketManager
    self.has_websocket = True
    self.set_rpc_manager(GUnicornWebSocketManager(self, self.session_max_duration, self.session_max_memory_duration, debug = debug))
    
  def use_ajax(self, debug = False):
    from fullpy.server.ajax import AjaxManager
    self.has_ajax    = True
    self.set_rpc_manager(AjaxManager(self, self.session_max_duration, self.session_max_memory_duration, debug = debug))
    
  def set_rpc_manager(self, rpc_manager):
    self.rpc_manager = rpc_manager
    if self.group_class:    rpc_manager.Group   = self.group_class
    if self.session_class:  rpc_manager.Session = self.session_class
    if self.has_session:    self.rpc(rpc_manager.server_new_session_id)
    
  def rpc(self, func, name = ""):
    setattr(self, name or func.__name__, func)
    self.rpc_funcs[name or func.__name__] = func
    return func
  
  def __getattr__(self, attr):
    if self.has_websocket and attr.startswith("client_"):
      def specific_client_call(session_or_group, *args, func_name = attr[7:], async_callback = None):
        return self.rpc_manager._client_call(session_or_group, async_callback, func_name, *args)
      setattr(self, attr, specific_client_call)
      return specific_client_call
    raise AttributeError(attr)
  
  def close_sessions(self):
    if self.rpc_manager: self.rpc_manager.close_sessions()
    
  def start(self, app, server_url, url_prefix = ""):
    self.server_url          = server_url
    self.url_prefix          = url_prefix
    
    app.register_blueprint(self.blueprint, url_prefix = "%s/%s" % (url_prefix, self.name))
    
    self.has_initial_data = not self.__class__.get_initial_data is ServerSideWebapp.get_initial_data
    
    if self.has_websocket:
      self.rpc_manager.route(app, "%s/%s/_websocket" % (url_prefix, self.name))
      
    if self.has_ajax:
      self.rpc_manager.route(app, "%s/%s/_ajax/" % (url_prefix, self.name))
        
    if self.has_session and self.rpc_manager:
      app.teardown_request(self.rpc_manager.destroy_timed_out_session_ids)
      if self.has_ajax:
        app.teardown_request(self.rpc_manager.destroy_timed_out_sessions)
      if self.persistent_session:
        app.teardown_request(self.rpc_manager.destroy_timed_out_persistent_sessions)
        
    if self.client_file: self.compile_client()
    
  def compile_client(self):
    from fullpy.server.compile_brython import compile_client
    ignored_modules = ["owlready2"]
    if not self.has_ajax:
      ignored_modules.extend(["_ajax", "browser.ajax", "fullpy.client.ajax"])
    if not self.has_websocket:
      ignored_modules.extend(["browser.websocket", "fullpy.client.websocket"])
      if not self.has_session: ignored_modules.extend(["fullpy.client.auth"])
      if not self.has_auth:    ignored_modules.extend(["hashlib"])
    compile_client(self.static_folder, [self.client_file], self.name, self.force_brython_compilation, self.minify_python_code, ignored_modules, [os.getcwd(), os.path.dirname(self.client_file)])
    
  def get_initial_data(self, url_params): return None
  
  def html_index(self):
    if self._html_index1 is None:
      html1  = """<!DOCTYPE html>\n<html><head><title>%s</title>\n""" % self.title
      html2  = ""
      
      has_jquery = False
      for js  in self.js :
        if not (js.startswith("http:") or js.startswith("https:")): js = flask.url_for("%s.static" % self.name, filename = js)
        html1 += """<script type="text/javascript" src="%s"></script>\n""" % js
        if js.startswith("jquery"): has_jquery = True
        
      for css in self.css:
        if not (css.startswith("http:") or css.startswith("https:")): css = flask.url_for("%s.static" % self.name, filename = css)
        html1 += """<link rel="stylesheet" href="%s"/>\n""" % css
        
      if self.favicon:
        html1 += """<link rel="icon" type="image/png" href="%s"/>\n""" % flask.url_for("%s.static" % self.name, filename = self.favicon)
        
      html1 += """</head><body onload="brython(0)">\n"""
      
      if has_jquery:
        html1 += """<script type="text/javascript">function jq(ref) { return $(ref) }</script>\n"""
      if self.has_auth:
        html1 += """<script type="text/javascript">$B.VFS["crypto_js.rollups.sha256"] = [ ".js", "/* CryptoJS v3.1.2 code.google.com/p/crypto-js (c) 2009-2013 by Jeff Mott. All rights reserved. code.google.com/p/crypto-js/wiki/License */ var CryptoJS=CryptoJS||function(h,s){var f={},t=f.lib={},g=function(){},j=t.Base={extend:function(a){g.prototype=this;var c=new g;a&&c.mixIn(a);c.hasOwnProperty('init')||(c.init=function(){c.$super.init.apply(this,arguments)});c.init.prototype=c;c.$super=this;return c},create:function(){var a=this.extend();a.init.apply(a,arguments);return a},init:function(){},mixIn:function(a){for(var c in a)a.hasOwnProperty(c)&&(this[c]=a[c]);a.hasOwnProperty('toString')&&(this.toString=a.toString)},clone:function(){return this.init.prototype.extend(this)}}, q=t.WordArray=j.extend({init:function(a,c){a=this.words=a||[];this.sigBytes=c!=s?c:4*a.length},toString:function(a){return(a||u).stringify(this)},concat:function(a){var c=this.words,d=a.words,b=this.sigBytes;a=a.sigBytes;this.clamp();if(b%4)for(var e=0;e<a;e++)c[b+e>>>2]|=(d[e>>>2]>>>24-8*(e%4)&255)<<24-8*((b+e)%4);else if(65535<d.length)for(e=0;e<a;e+=4)c[b+e>>>2]=d[e>>>2];else c.push.apply(c,d);this.sigBytes+=a;return this},clamp:function(){var a=this.words,c=this.sigBytes;a[c>>>2]&=4294967295<< 32-8*(c%4);a.length=h.ceil(c/4)},clone:function(){var a=j.clone.call(this);a.words=this.words.slice(0);return a},random:function(a){for(var c=[],d=0;d<a;d+=4)c.push(4294967296*h.random()|0);return new q.init(c,a)}}),v=f.enc={},u=v.Hex={stringify:function(a){var c=a.words;a=a.sigBytes;for(var d=[],b=0;b<a;b++){var e=c[b>>>2]>>>24-8*(b%4)&255;d.push((e>>>4).toString(16));d.push((e&15).toString(16))}return d.join('')},parse:function(a){for(var c=a.length,d=[],b=0;b<c;b+=2)d[b>>>3]|=parseInt(a.substr(b, 2),16)<<24-4*(b%8);return new q.init(d,c/2)}},k=v.Latin1={stringify:function(a){var c=a.words;a=a.sigBytes;for(var d=[],b=0;b<a;b++)d.push(String.fromCharCode(c[b>>>2]>>>24-8*(b%4)&255));return d.join('')},parse:function(a){for(var c=a.length,d=[],b=0;b<c;b++)d[b>>>2]|=(a.charCodeAt(b)&255)<<24-8*(b%4);return new q.init(d,c)}},l=v.Utf8={stringify:function(a){try{return decodeURIComponent(escape(k.stringify(a)))}catch(c){throw Error('Malformed UTF-8 data');}},parse:function(a){return k.parse(unescape(encodeURIComponent(a)))}}, x=t.BufferedBlockAlgorithm=j.extend({reset:function(){this._data=new q.init;this._nDataBytes=0},_append:function(a){'string'==typeof a&&(a=l.parse(a));this._data.concat(a);this._nDataBytes+=a.sigBytes},_process:function(a){var c=this._data,d=c.words,b=c.sigBytes,e=this.blockSize,f=b/(4*e),f=a?h.ceil(f):h.max((f|0)-this._minBufferSize,0);a=f*e;b=h.min(4*a,b);if(a){for(var m=0;m<a;m+=e)this._doProcessBlock(d,m);m=d.splice(0,a);c.sigBytes-=b}return new q.init(m,b)},clone:function(){var a=j.clone.call(this); a._data=this._data.clone();return a},_minBufferSize:0});t.Hasher=x.extend({cfg:j.extend(),init:function(a){this.cfg=this.cfg.extend(a);this.reset()},reset:function(){x.reset.call(this);this._doReset()},update:function(a){this._append(a);this._process();return this},finalize:function(a){a&&this._append(a);return this._doFinalize()},blockSize:16,_createHelper:function(a){return function(c,d){return(new a.init(d)).finalize(c)}},_createHmacHelper:function(a){return function(c,d){return(new w.HMAC.init(a, d)).finalize(c)}}});var w=f.algo={};return f}(Math); (function(h){for(var s=CryptoJS,f=s.lib,t=f.WordArray,g=f.Hasher,f=s.algo,j=[],q=[],v=function(a){return 4294967296*(a-(a|0))|0},u=2,k=0;64>k;){var l;a:{l=u;for(var x=h.sqrt(l),w=2;w<=x;w++)if(!(l%w)){l=!1;break a}l=!0}l&&(8>k&&(j[k]=v(h.pow(u,0.5))),q[k]=v(h.pow(u,1/3)),k++);u++}var a=[],f=f.SHA256=g.extend({_doReset:function(){this._hash=new t.init(j.slice(0))},_doProcessBlock:function(c,d){for(var b=this._hash.words,e=b[0],f=b[1],m=b[2],h=b[3],p=b[4],j=b[5],k=b[6],l=b[7],n=0;64>n;n++){if(16>n)a[n]= c[d+n]|0;else{var r=a[n-15],g=a[n-2];a[n]=((r<<25|r>>>7)^(r<<14|r>>>18)^r>>>3)+a[n-7]+((g<<15|g>>>17)^(g<<13|g>>>19)^g>>>10)+a[n-16]}r=l+((p<<26|p>>>6)^(p<<21|p>>>11)^(p<<7|p>>>25))+(p&j^~p&k)+q[n]+a[n];g=((e<<30|e>>>2)^(e<<19|e>>>13)^(e<<10|e>>>22))+(e&f^e&m^f&m);l=k;k=j;j=p;p=h+r|0;h=m;m=f;f=e;e=r+g|0}b[0]=b[0]+e|0;b[1]=b[1]+f|0;b[2]=b[2]+m|0;b[3]=b[3]+h|0;b[4]=b[4]+p|0;b[5]=b[5]+j|0;b[6]=b[6]+k|0;b[7]=b[7]+l|0},_doFinalize:function(){var a=this._data,d=a.words,b=8*this._nDataBytes,e=8*a.sigBytes; d[e>>>5]|=128<<24-e%32;d[(e+64>>>9<<4)+14]=h.floor(b/4294967296);d[(e+64>>>9<<4)+15]=b;a.sigBytes=4*d.length;this._process();return this._hash},clone:function(){var a=g.clone.call(this);a._hash=this._hash.clone();return a}});s.SHA256=g._createHelper(f);s.HmacSHA256=g._createHmacHelper(f)})(Math); " ];</script>\n"""
        
      html1 += """<div id="main_content">\n"""
      html1 += self.html_content()
      html1 += """</div>\n"""
      
      if self.has_python_client:
        html1 += """<script type="text/python">
from browser import window
"""
        html1 += """window.WEBAPP_OPTS = { "fullpy" : { "name" : "%s" } }\n""" % self.name
        
        #if self.has_session:
        #  html1 += """window.WEBAPP_OPTS["session"] = { "client_reloadable_session" : %s""" % self.client_reloadable_session
        #  html2 += """ }\n"""
        
        #if self.has_serializer:
        #  html2 += """window.WEBAPP_OPTS["serializer"] = { "ignore_none" : %s, "ignore_empty_list" : %s }\n""" % (self.serializer.ignore_none, self.serializer.ignore_empty_list)
          
        if self.has_websocket:
          html2 += """window.WEBAPP_OPTS["websocket"] = { "debug" : %s }\n""" % self.rpc_manager.debug
          #html2 += """import fullpy.client.websocket\n"""
          
        if self.has_ajax:
          html2 += """window.WEBAPP_OPTS["ajax"] = { "debug" : %s }\n""" % self.rpc_manager.debug
          #html2 += """import fullpy.client.ajax\n"""
          
        html2 += """import %s\n""" % self.client_module
        html2 += """</script>\n"""
        
      html2 += """<div id="popup_window" style="display: none;"></div>\n"""
      html2 += """</body></html>\n"""
      
      if (not self.has_initial_data) and (not self.has_session):
        self._html_index1 = "%s%s" % (html1, html2)
      else:
        self._html_index1 = html1
        self._html_index2 = html2
        
    if self.has_initial_data:
      TRANS.lang = flask.request.args.get("lang") or flask.request.headers["Accept-Language"][:2] or TRANS.default_lang
      #flask.request.accept_languages.best_match()
      
      initial_data = self.get_initial_data(flask.request.args)
      if self.has_session:
        r = flask.Response("""%simport fullpy.client\nfullpy.client._initial_data = %s\nwindow.WEBAPP_OPTS["session"] = { "client_reloadable_session" : %s, "session_id" : "%s" }\n%s""" % (self._html_index1, repr(initial_data), self.client_reloadable_session, self.server_new_session_id(), self._html_index2))
        r.headers["Cache-Control"] = "no-cache, no-store, max-age=0, must-revalidate"
      else:
        r = flask.Response("""%simport fullpy.client\nfullpy.client._initial_data = %s\n%s""" % (self._html_index1, repr(initial_data), self._html_index2))
    else:
      if self.has_session:
        r = flask.Response("""%swindow.WEBAPP_OPTS["session"] = { "client_reloadable_session" : %s, "session_id" : "%s" }\n%s""" % (self._html_index1, self.client_reloadable_session, self.server_new_session_id(), self._html_index2))
        r.headers["Cache-Control"] = "no-cache, no-store, max-age=0, must-revalidate"
      else:
        r = flask.Response(self._html_index1)
    return r
  
  def html_content(self):
    return """<div style="text-align: center; margin-top: 10em;"><b>Please wait...</b></div>"""
  
  def server_set_lang(self, session, lang):
    TRANS.set_lang(lang)
    if session:
      if session.user: session.user.webapp_lang = lang
      else:            session.     webapp_lang = lang
    
