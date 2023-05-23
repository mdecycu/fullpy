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

import sys, atexit, flask


def serve_forever(webapps, address = "http://127.0.0.1:5000", url_prefix = "", flask_app = None):
  flask_app = flask_app or flask.Flask("fullpy")
  static_files = {}
  for webapp in webapps:
    webapp.start(flask_app, address, url_prefix)
    if webapp.static_folder:
      static_files["%s/%s/static" % (url_prefix, webapp.name)] = webapp.static_folder
      
  def cleanup():
    for webapp in webapps:
      webapp.close_sessions()
      if webapp.world: webapp.world.save()
  atexit.register(cleanup)
  
  return flask_app
