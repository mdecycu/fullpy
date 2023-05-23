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

import sys, os, os.path

def getmtime(path, default = 0):
  try:                      return os.path.getmtime(path)
  except FileNotFoundError: return default


blacklisted_modules = [ "posix", "posixpath", "traceback", "typing", "ast", "_dummy_thread", "argparse", "doctest", "importlib", "importlib.machinery", "importlib.util", "importlib._bootstrap", "importlib._bootstrap_external" ]

def compile_client(static_folder, client_files = [], webapp_name = "", force = False, minify_python_code = False, ignored_modules = [], extra_python_path = []):
  if not os.access(static_folder, os.W_OK):
    print("\n* FullPy * Skip client Brython compilation of webapp %s ; %s is not writable!" % (webapp_name, static_folder), file = sys.stderr)
    return
  
  # brython_js     = os.path.join(os.path.dirname(brython.__file__), "data", "brython.js")
  # brython_stdlib = os.path.join(os.path.dirname(brython.__file__), "data", "brython_stdlib.js")
  
  # static_js     = os.path.join(static_folder, "brython.js")
  # static_stdlib = os.path.join(static_folder, "brython_stdlib.js")
  
  # import brython, shutil
  # if (not os.path.exists(static_js)) or (os.path.getmtime(static_js) < os.path.getmtime(brython_js)):
  #   print("cp", brython_js, static_js, file = sys.stderr)
  #   shutil.copyfile(brython_js, static_js)
  #   force = True
  # if (not os.path.exists(static_stdlib)) or (os.path.getmtime(static_stdlib) < os.path.getmtime(brython_stdlib)):
  #   print("cp", brython_stdlib, static_stdlib, file = sys.stderr)
  #   shutil.copyfile(brython_stdlib, static_stdlib)
  #   force = True
  
  if webapp_name:
    BRYTHON_MODULE = os.path.join(static_folder, "%s_brython_modules.js" % webapp_name)
    PY_LIST        = os.path.join(static_folder, "%s_py_list.txt" % webapp_name)
  else:
    BRYTHON_MODULE = os.path.join(static_folder, "brython_modules.js")
    PY_LIST        = os.path.join(static_folder, "py_list.txt")
    
  brython_module_mtime = getmtime(BRYTHON_MODULE)
  
  if (not force) and os.path.exists(PY_LIST):
    for py_file in open(PY_LIST).read().split("\n"):
      if getmtime(py_file, brython_module_mtime + 1) > brython_module_mtime: break
    else:
      return # No changes
    
  print("\n* FullPy * Compile webapp '%s' client with Brython :" % webapp_name, file = sys.stderr)
  def do(s):
    print("%s" % s, file = sys.stderr)
    return os.system(s)
  import tempfile
  with tempfile.TemporaryDirectory() as tmp_dir:
    modules = []
    cmds    = []
    subdirs = set()
    for file0 in client_files:
      module = os.path.splitext(os.path.basename(file0))[0]
      file = os.path.dirname(file0)
      module_paths = []
      while os.path.exists(os.path.join(file, "__init__.py")):
        module_paths.insert(0, os.path.basename(file))
        file = os.path.dirname(file)
      module = ".".join(module_paths + [module])
      modules.append(module)
      for i in range(len(module_paths)): subdirs.add(os.path.join(tmp_dir, *module_paths[:i+1]))
      cmds.append("""cp %s %s""" % (file0, os.path.join(tmp_dir, *module.split(".")[:-1])))
    print("Including the following modules: %s, and their dependencies..." % ", ".join(modules), file = sys.stderr)
    do("""cp %s %s""" % (os.path.join(static_folder, "brython_stdlib.js"), tmp_dir))
    for subdir in sorted(subdirs, key = lambda i: len(i)): do("""mkdir %s""" % subdir)
    for cmd in cmds: do(cmd)
    
    with open(os.path.join(tmp_dir, "index.html"), "w") as index:
      index.write("""<html>
<head>
<script src="brython.js"></script>
<script src="brython_stdlib.js"></script>
</head>
<body>
<script type="text/python">
from browser import window
%s
</script>
</body>
</html>""" % "\n".join("import %s" % module for module in modules))
    
    
    ignored_modules = blacklisted_modules + ignored_modules
    
    with open(os.path.join(tmp_dir, "brython_compile.py"), "w") as py:
      if minify_python_code: py.write("""import python_minifier\n""")
      else:                  py.write("""python_minifier = None\n""")
      py.write("""ignored_modules = set(%s)
""" % ignored_modules)
      py.write("""
import sys, os, os.path, importlib.util
from brython.list_modules import *

sys.path.extend(%s)

      """ % extra_python_path)

      py.write("""
stdlib_dir, stdlib = load_stdlib_sitepackages()
user_modules       = {}
py_files           = []

def get_package(filename):
   package_parts = []
   dirname = os.path.dirname(filename)
   while os.path.exists(os.path.join(dirname, "__init__.py")):
     package_parts.insert(0, os.path.basename(dirname))
     dirname = os.path.dirname(dirname)
     
   package = ".".join(filter(None, package_parts))
   if package.startswith('Lib.site-packages.'): package = package[len('Lib.site-packages.'):]
   
   basename  = os.path.basename(filename)
   name, ext = os.path.splitext(basename)
   if   basename == "__init__.py": module_name = package
   elif not package:               module_name = name
   else:                           module_name = "%s.%s" % (package, name)
   
   return package, module_name     
   
def load_script(path):
  module_name, ext, src, imports = load(path)

  parent_module_name = module_name
  while "." in parent_module_name:
    parent_module_name = parent_module_name.rsplit(".", 1)[0]
    if not parent_module_name in imports: imports.append(parent_module_name)
    
  if src: print("load script %s:" % path, module_name, ":", ext, imports)
  
  for name in imports: load_user_module(name)
    
def load_user_module(name):
  if (name in stdlib) or (name in user_modules): return
  
  path = None
  try:
    spec = importlib.util.find_spec(name)
    if not spec:
      print("Warning: cannot load module '%s'!" % name)
      return
    path = spec.origin
  except: pass
  
  if path is None:
    module_path = "%s.py" % (name.replace(".", os.sep))
    for python_path in sys.path:
      p = os.path.join(python_path, module_path) 
      if os.path.exists(p):
        path = p
        break
      
  if path is None:
    #logger.error("Unable to find module %s", name)
    return
  
  module_name, ext, src, imports = load(path)
  if src: print("load module %s:" % name, module_name, ":", ext, imports)
  
  for name2 in imports: load_user_module(name2)
  
def load(path):
  py_files.append(path)
  name, ext            = os.path.splitext(os.path.basename(path))
  package, module_name = get_package(path)
  
  if module_name in ignored_modules: return module_name, ext, "", []
  
  with open(path, encoding = "utf-8") as fobj:
    try:
      src = fobj.read()
    except:
      logger.error("Unable to read %s", path)
      return "", "", "", []
      
  mf = ModulesFinder(os.path.dirname(path))
  imports = sorted(list(mf.get_imports(src)))
  if "" in imports: imports.remove("")
  for i, module in enumerate(imports):
    if module.startswith("."): imports[i] = "%s%s" % (name, module)
    
  if python_minifier:
    src = python_minifier.minify(src, hoist_literals = False, rename_locals = False, rename_globals = False, convert_posargs_to_args = False)
      
  user_modules[module_name] = [ext, src, imports]
  if module_name == package: user_modules[module_name].append(1)
  return module_name, ext, src, imports
  
""")
      
      for file in client_files:   py.write("""load_script     ("%s")\n""" % os.path.abspath(file))
      
      py.write("""open("%s", "w").write("\\n".join(py_files))\n""" % PY_LIST)
      py.write("""
#print("User modules:", ", ".join(sorted(user_modules.keys())))

for module in ignored_modules:
  if module in stdlib:
    stdlib[module] = [".py", "", []]

finder = ModulesFinder(stdlib = stdlib, user_modules = user_modules)
finder.inspect()
finder.make_brython_modules("./brython_modules.js")

print("Included modules:", ", ".join(sorted(list(module for module in finder.modules if not module in ignored_modules))))
""")

      if 0:
        py.write("""
def scan(module):
  print()
  l  = list(module for module in finder.modules if not module in ignored_modules)
  l2 = []
  for i in l:
    if i in user_modules: nb = len(user_modules[i][1])
    else:                 nb = len(stdlib[i][1])
    l2.append((i, nb))
  for i, nb in sorted(l2, key = lambda x: x[1]): print(nb, i)
  print(sum(nb for i, nb in sorted(l2)))
  print()

  l = [[i] for i in user_modules.keys()]
  nb = 1
  while True:
    if not l: return None
    nb += 1
    l2 = []
    for nav in l:
      last_mod = stdlib.get(nav[-1]) or user_modules.get(nav[-1])
      if not last_mod: continue
      if len(last_mod) < 3: continue
      for next_mod in last_mod[2]:
        if next_mod in nav: continue
        if next_mod == module:
          print(" > ".join(nav + [next_mod]))
          return
        l2.append(nav + [next_mod])
    l = l2
scan("re")
""")
    
    do("""cd %s; %s brython_compile.py""" % (tmp_dir, sys.executable))
    do("""cp %s %s""" % (os.path.join(tmp_dir, "brython_modules.js"), BRYTHON_MODULE))
    
  print("* FullPy * End of webapp client compilation\n", file = sys.stderr)
