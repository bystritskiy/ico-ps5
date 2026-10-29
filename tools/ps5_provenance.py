"""Local source identity shared by the native builder and packager."""
import hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def source_identity():
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0')
    digest=hashlib.sha256()
    for raw in sorted(set(n for n in names if n)):
        path=ROOT/raw.decode('utf-8')
        digest.update(raw+b'\0')
        if path.is_file():
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        else:
            digest.update(b'missing')
    return {
        'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'working_tree_sha256':digest.hexdigest(),
    }
