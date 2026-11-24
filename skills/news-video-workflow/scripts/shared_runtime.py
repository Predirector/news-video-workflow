"""Versioned, machine-local environments. Never replace existing project environments."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json,os,platform,subprocess,sys,time

def cache_root():
 override=os.environ.get('NEWS_RUNTIME_ROOT')
 if override:return Path(override).expanduser().resolve()
 base=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local')) if os.name=='nt' else Path.home()/'.local/share'
 return base/'news-video-workflow/runtimes'

def pool(kind,inputs):
 identity={'kind':kind,'system':platform.system(),'arch':platform.machine(),'inputs':inputs}
 if kind in ('python','tools'):identity.update(python=sys.version,executable=str(Path(sys.executable).resolve()))
 if kind in ('node','tools'):identity['node']=subprocess.check_output(['node','-p','process.versions.modules'],text=True).strip()
 key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
 return cache_root()/kind/key

@contextmanager
def locked(directory):
 directory.parent.mkdir(parents=True,exist_ok=True);lock=directory.with_name(directory.name+'.lock');deadline=time.monotonic()+300
 while True:
  try:lock.mkdir();break
  except FileExistsError:
   if time.monotonic()>deadline:raise RuntimeError('Shared runtime busy: '+str(lock)+'. Inspect the owning installer; do not delete an active lock.')
   time.sleep(1)
 try:directory.mkdir(exist_ok=True);yield directory
 finally:lock.rmdir()

def is_reference(path):
 p=Path(path);return p.is_symlink() or getattr(p,'is_junction',lambda:False)()

def link(target,destination):
 target=Path(target);destination=Path(destination)
 if is_reference(destination) or destination.exists():
  if destination.resolve()!=target.resolve():raise RuntimeError('Existing environment preserved: '+str(destination)+'. Use --local or migrate explicitly after validation.')
  return
 if os.name=='nt':subprocess.run(['cmd','/c','mklink','/J',str(destination),str(target.resolve())],check=True,capture_output=True)
 else:destination.symlink_to(target.resolve(),target_is_directory=True)

def record(root,kind,target):
 p=Path(root)/'runtime-links.local.json';d=json.loads(p.read_text()) if p.exists() else {};d[kind]=str(Path(target).resolve());p.write_text(json.dumps(d,indent=2)+'\n')
