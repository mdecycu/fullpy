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


import sys, gevent, gevent.lock, gevent.event


# import weakref
# _IMMEDIATE_NOTIFIERS = weakref.WeakValueDictionary()

# class _WriteImmediateNotifier(gevent.lock.BoundedSemaphore):
#   def __init__(self, write_lock, link):
#     gevent.lock.BoundedSemaphore.__init__(self)
#     self.pair        = write_lock.pair
#     self.current     = gevent.getcurrent()
#     self._notify_all = False
#     _IMMEDIATE_NOTIFIERS[link.link] = self
#     self.rawlink(link)
#   def ready(self):
#     return bool(self.pair.data_access_sem.ready() or
#                (self.pair.write_owner is self.current) or
#                (self.pair.nb_readers and set(self.read_owners) == { gevent.getcurrent() }))
  
# class _WrappedLink(object):
#   def __init__(self, lock, link):
#     self.lock = lock
#     self.link = link
#     self.called = False
#   def __call__(self, _drop_it):
#     if not self.called:
#       self.called = True
#       self.link(self.lock)
#   def __eq__  (self, other): return other is self.link
  
class _ReadLock(object):
  def __init__(self, pair): self.pair = pair
  def ready(self): return self.pair.ready_read()
  def acquire(self): self.pair.acquire_read()
  def release(self): self.pair.release_read()
  def __enter__(self):                        self.pair.acquire_read()
  def __exit__(self, type, value, traceback): self.pair.release_read()
  def debug(self): self.pair.debug()
  
  def rawlink(self, f):
    f2 = _WrappedLink(self, f)
    if self.pair.ready_read(): _notify(f2)
    else:
      self.pair.data_access_sem.rawlink(f2)
      self.pair.can_read_event .rawlink(f2)
      
  def unlink(self, f):
    self.pair.data_access_sem.unlink(f)
    self.pair.can_read_event .unlink(f)

  def acquired_with(self, objects):
    if all(o.ready() for o in objects) and self.ready(): return self
    return _ReadAquiredWith(self, objects)
  
class _ReadAquiredWith(object):
  def __init__(self, lock, objects):
    self.lock    = lock
    self.objects = objects
    
  def __enter__(self):
    data_access_sem = self.lock.pair.data_access_sem
    can_read_event  = self.lock.pair.can_read_event
    while True:
      gevent.wait(self.objects)
      if not self.lock.ready():
        gevent.wait([self.lock.pair.data_access_sem, self.lock.pair.can_read_event], count = 1)
      if all(o.ready() for o in self.objects) and self.lock.ready(): break
      
    self.lock.__enter__()
    
  def __exit__(self, type, value, traceback): self.lock.__exit__(type, value, traceback)

  
class _WriteLock(object):
  def __init__(self, pair):
    self.pair = pair
    
  def ready(self): return self.pair.ready_write()
  def acquire(self): self.pair.acquire_write()
  def release(self): self.pair.release_write()
  def __enter__(self):                        self.pair.acquire_write()
  def __exit__(self, type, value, traceback): self.pair.release_write()
  def debug(self): self.pair.debug()
  
  # def rawlink(self, f):
  #   f2 = _WrappedLink(self, f)
  #   if (self.pair.write_owner is gevent.getcurrent()) or (self.pair.nb_readers and set(self.read_owners) == { gevent.getcurrent() }):
  #     _WriteImmediateNotifier(self, f2)
  #   self.pair.data_access_sem.rawlink(f2)
  
  # def unlink(self, f):
  #   self.pair.data_access_sem.unlink(f)
  #   if f in _IMMEDIATE_NOTIFIERS: _IMMEDIATE_NOTIFIERS[f].unlink(f)
  
  def acquired_with(self, objects):
    if all(o.ready() for o in objects) and self.ready(): return self
    return _WriteAquiredWith(self, objects)
  
class _WriteAquiredWith(object):
  def __init__(self, lock, objects):
    self.lock    = lock
    self.objects = objects
    
  def __enter__(self):
    objects = [self.lock.pair.data_access_sem, *self.objects]
    while True:
      gevent.wait(objects)
      if all(o.ready() for o in objects): break
    self.lock.__enter__()
    
  def __exit__(self, type, value, traceback): self.lock.__exit__(type, value, traceback)
    
    
class _DebugBoundedSemaphore(gevent.lock.BoundedSemaphore):
  def __init__(self, timeout, debug):
    gevent.lock.BoundedSemaphore.__init__(self)
    self.timeout = timeout
    self.debug   = debug
    self.waiters = []
    
  def acquire(self, block = True, timeout = None):
    self.waiters.append(gevent.getcurrent())
    if not gevent.lock.BoundedSemaphore.acquire(self, block, timeout or self.timeout): self.debug(True)
    self.waiters.remove(gevent.getcurrent())
    self.owner = gevent.getcurrent()
    
  def release(self):
    gevent.lock.BoundedSemaphore.release(self)
    self.owner = None
    
  def __enter__(self):                        self.acquire()
  def __exit__(self, type, value, traceback): self.release()
    
class _DebugEvent(gevent.event.Event):
  def __init__(self, timeout, debug):
    gevent.event.Event.__init__(self)
    self.timeout = timeout
    self.debug   = debug
    self.waiters = []
  def wait(self, timeout = None):
    self.waiters.append(gevent.getcurrent())
    if not gevent.event.Event.wait(self, timeout or self.timeout): self.debug(True)
    self.waiters.remove(gevent.getcurrent())
    
class _ReadWriteLockPair(object):
  def __init__(self, timeout_bomb = 0, verbose = False):
    self.nb_readers      = 0
    self.nb_writers      = 0
    self.write_owner     = None
    self.read_owners     = []
    self.writers_waiting = 0
    self.readers_waiting = 0
    self.priority        = None
    self.last_read_upgraded_to_write = None
    
    if timeout_bomb:
      self.data_access_sem = _DebugBoundedSemaphore(timeout_bomb, self.debug)
      self.can_read_event  = _DebugEvent(timeout_bomb, self.debug)
      self.priority_event  = _DebugEvent(timeout_bomb, self.debug)
    else:
      self.data_access_sem = gevent.lock.BoundedSemaphore()
      self.can_read_event  = gevent.event.Event()
      self.priority_event  = gevent.event.Event()
      
    if verbose:
      self.acquire_read  = self.acquire_read_verbose
      self.release_read  = self.release_read_verbose
      self.acquire_write = self.acquire_write_verbose
      self.release_write = self.release_write_verbose
      
    self.read_lock  = _ReadLock (self)
    self.write_lock = _WriteLock(self)
      
  def ready_write(self):
    return  bool(self.data_access_sem.ready() or
                (self.write_owner is gevent.getcurrent()) or
                (self.nb_readers and set(self.read_owners) == { gevent.getcurrent() }))
  
  def acquire_write(self):
    self.can_read_event.clear()
    
    if self.write_owner is gevent.getcurrent():
      self.nb_writers += 1
      
    elif self.nb_readers and (gevent.getcurrent() in self.read_owners):
      if self.last_read_upgraded_to_write and (not self.last_read_upgraded_to_write is gevent.getcurrent()) and (not self.last_read_upgraded_to_write.dead):
        raise ValueError("Only a single greenlet is allowed to acquire write lock while owning read lock! Greenlets are: %s (previous, still running) and %s (current)." % (self.last_read_upgraded_to_write, gevent.getcurrent()))
      self.last_read_upgraded_to_write = gevent.getcurrent()
      
      if len(set(self.read_owners)) > 1: # Current is not the only reader
        self.priority = gevent.getcurrent()
        try:
          self.priority_event.wait()
        finally:
          self.priority = None
          self.priority_event.clear()
          
      self.nb_readers  = 0
      self.nb_writers  = 1
      self.write_owner = gevent.getcurrent()
      
    else:
      self.writers_waiting += 1
      try:     self.data_access_sem.acquire() # Can wait => May be killed at this point.
      finally: self.writers_waiting -= 1
      
      self.nb_writers  = 1
      self.write_owner = gevent.getcurrent()
      
  def release_write(self):
    if not self.write_owner is gevent.getcurrent():
      self.debug()
      raise ValueError("Cannot unlock, not owner! Owner is '%s', current is '%s'." % (self.write_owner, gevent.current()))
    
    if self.nb_writers == 1:
      self.nb_writers  = 0
      self.write_owner = None
      if self.read_owners: self.nb_readers = len(self.read_owners) # Was reading before obtaining write permissions
      self.set_ready()
    else:
      self.nb_writers -= 1
      
  def set_ready(self):
    if (self.nb_writers == 0) and (self.nb_readers == 0):
      self.data_access_sem.release()
      
    if (not self.writers_waiting) and self.readers_waiting:
      self.can_read_event.set()
      
  def ready_read(self):
    return  bool((self.write_owner is gevent.getcurrent()) or
                 (self.nb_readers and (gevent.getcurrent() in self.read_owners)) or
                 ((not self.writers_waiting) and (self.data_access_sem.ready() or self.nb_readers)))
  
  def acquire_read(self):
    if self.write_owner is gevent.getcurrent(): return # Ok: write permissions implies read permissions
    
    if self.nb_readers and (gevent.getcurrent() in self.read_owners):
      self.nb_readers += 1
      self.read_owners.append(gevent.getcurrent())
      return
    
    while True:
      if not(self.nb_writers or self.writers_waiting):
        if self.nb_readers == 0:
          assert self.data_access_sem.ready()
          self.data_access_sem.acquire()
        self.nb_readers += 1
        self.read_owners.append(gevent.getcurrent())
        return
        
      self.readers_waiting += 1
      try:     self.can_read_event.wait() # Can wait => May be killed at this point.
      finally: self.readers_waiting -= 1
      
      if self.write_owner or self.writers_waiting: gevent.sleep(0)
      
  def release_read(self):
    if self.write_owner is gevent.getcurrent(): return # Ok: write permissions implies read permissions
    
    self.read_owners.remove(gevent.getcurrent())
    self.nb_readers -= 1
    
    if self.nb_readers == 0: self.set_ready()
    elif self.priority and (set(self.read_owners) == { self.priority }): self.priority_event.set()
    
  def _get_current_greenlet_name(self):
    current = gevent.getcurrent()
    return "Greenlet %s running %s" % (hex(id(current)), current._run)
  
  def acquire_write_verbose(self):
    print("    ACQUIRE WRITE", self._get_current_greenlet_name())
    self.acquire_write()
    
  def release_write_verbose(self):
    print("    RELEASE WRITE", self._get_current_greenlet_name())
    self.release_write()
    
  def acquire_read_verbose(self):
    print("    ACQUIRE READ ", self._get_current_greenlet_name())
    self.acquire_read()
    
  def release_read_verbose(self):
    print("    RELEASE READ ", self._get_current_greenlet_name())
    self.release_read()
    
  def debug(self, bomb = False):
    if bomb:
      print(file = sys.stderr)
      print(" ---------- TIME OUT BOMB! Dead-lock detected ----------", file = sys.stderr)
    print(file = sys.stderr)
    print("Debug read/write lock pair %s/%s:" % (self.read_lock, self.write_lock), file = sys.stderr)
    print("    Data access semaphore:       %s, ready: %s" % (self.data_access_sem, self.data_access_sem.ready()), file = sys.stderr)
    if hasattr(self.data_access_sem, "owner"):
      print("    Data access semaphore owner: %s" % self.data_access_sem.owner, file = sys.stderr)
    print("    Writer: %s (acquired %s time(s))" % (self.write_owner, self.nb_writers), file = sys.stderr)
    print("    Writers waiting: %s" % self.writers_waiting, file = sys.stderr)
    print("    Readers: %s %s" % (len(self.read_owners), self.read_owners), file = sys.stderr)
    print("    Readers waiting: %s" % self.readers_waiting, file = sys.stderr)
    print(file = sys.stderr)
    if bomb:
      import traceback
      print(file = sys.stderr)
      waiters = set(self.data_access_sem.waiters + self.can_read_event.waiters)
      if not self.data_access_sem.owner is None: waiters.add(self.data_access_sem.owner)
      waiters = sorted(waiters, key = lambda waiter: 1 if waiter is gevent.getcurrent() else 0)
      
      print("* %s greenlets involved: %s" % (len(waiters), ", ".join(hex(id(waiter)) for waiter in waiters)), file = sys.stderr)
      print(file = sys.stderr)
      waiter_2_repr = { waiter : "%s (%s)" % (hex(id(waiter)), waiter._run) for waiter in waiters }
      for waiter in waiters:
        names = []
        if waiter in self.data_access_sem.waiters: names.append("waiting for data_access_sem")
        if waiter in self.can_read_event .waiters: names.append("waiting for can_read_event")
        if waiter is self.data_access_sem.owner:   names.append("owns data_access_sem")
        
        print("***** %s:" % waiter_2_repr[waiter], ", ".join(names), file = sys.stderr)
        
        print(''.join(traceback.format_stack(waiter.gr_frame)), file = sys.stderr)


def ReadWriteLockPair(timeout_bomb = None, verbose = False):
  """Read/write lock allowing either multiple readers or a single writer at a time.
Both read and write locks are reentrant.
After acquire write lock, one can safely acquire the read lock (as a no-op).
After acquire read lock, a single greenlet can safely try to acquire the write lock to upgrade to write permission.
In case of multiple pending call to acquire, writers are always prioritized over readers.
The function returns a (read_lock, write_lock) pair."""
  lock_pair = _ReadWriteLockPair(timeout_bomb, verbose)
  return lock_pair.read_lock, lock_pair.write_lock

