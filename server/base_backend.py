# FullPy
# Copyright (C) 2022-2024 Jean-Baptiste LAMY
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

def _split_address(address):
  addresses = []
  for i in address.split(","):
    protocol, rest = i.split("://", 1)
    host, port = rest.rsplit(":", 1)
    port = int(port.split("/", 1)[0])
    addresses.append((protocol, host, port))
  return addresses
