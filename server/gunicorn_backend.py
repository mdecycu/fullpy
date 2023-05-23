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

__all__ = ["serve_forever"]

import sys, datetime, gunicorn.app.base, flask

from fullpy.server import _gevent_patch_translator

class Worker(object):
  CURRENT_WORKER = None
  
  def __init__(self):
    Worker.CURRENT_WORKER = self
    print(file = sys.stderr)
    
  def stop(self):
    Worker.CURRENT_WORKER = None
    

def _split_address(address):
  protocol, rest = address.split("://", 1)
  host, port = rest.split(":", 1)
  port = int(port.split("/", 1)[0])
  return protocol, host, port


def serve_forever(webapps, address = "http://127.0.0.1:5000", url_prefix = "", flask_app = None, log_file = None, nb_process = 1, max_nb_websockect = 5000, worker_class = None, use_gevent = False, gunicorn_options = None):
  
  flask_app = flask_app or flask.Flask("fullpy")
  flask_app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes = 30)
  
  for webapp in webapps:
    if webapp.has_websocket: use_gevent = True
    webapp.start(flask_app, address, url_prefix)
    
  if use_gevent:
    from gevent import monkey
    if not monkey.is_module_patched("socket"):
      raise RuntimeError("Websockets require GEvent; please call gevent.monkey.patch_all() at the beginning of the program!")
    _gevent_patch_translator()
    
  worker_class = worker_class or Worker
  
  protocol, host, port = _split_address(address)
  
  class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self):
      super().__init__()
      
    def load_config(self):
      self.cfg.set("workers", nb_process)
      self.cfg.set("max_requests", 2000)
      self.cfg.set("post_worker_init", self.post_worker_init)
      self.cfg.set("worker_exit", self.worker_exit)
      self.cfg.set("keepalive", 5)
      if use_gevent:
        self.cfg.set("worker_class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker")
        self.cfg.set("worker_connections", max_nb_websockect)
        
      self.cfg.set("bind", address[len(protocol) + 3:])
      if log_file:
        self.cfg.set("capture_output", True)
        self.cfg.set("errorlog", log_file)
        
      if gunicorn_options:
        for k, v in gunicorn_options: self.cfg.set(k, v)
        
    def load(self): return flask_app
    
    def post_worker_init(self, worker):
      worker.fullpy_worker = worker_class()
      
    def worker_exit(self, server, worker):
      worker.fullpy_worker.stop()
      webapp.close_sessions()
      if webapp.world: webapp.world.save()
      
  StandaloneApplication().run()
  
