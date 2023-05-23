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


# Notice that this source file is SHARED between client and server: both use it!

from fullpy.util import TRANS

TRANS.add_translations("fr", {
  "Hello from server" : "Bonjour de la part du serveur",
  "Hello from client" : "Bonjour de la part du client",
  "Language:" : "Langage :",
})

TRANS.add_translations("es", {
  "Hello from server" : "Hola desde el servidor",
  "Hello from client" : "Hola del cliente",
  "Language:" : "Idioma :",
})

TRANS.add_translations("it", {
  "Hello from server" : "Ciao dal server",
  "Hello from client" : "Ciao dal cliente",
  "Language:" : "Lingua :",
})

TRANS.add_translations("en", {
  "Language 'en'" : "English",
  "Language 'fr'" : "Français",
  "Language 'es'" : "Español",
  "Language 'it'" : "Italiano",

# English is not necessary for the following, because the translation key is already the English translation.

#  "Hello from server" : "Hello from server",
#  "Hello from client" : "Hello from client",
})
