import os, hashlib, datetime

def sha(f):
    with open(f,'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]

base = r'c:\Users\Sekar Harshitha\Downloads\build fast'
files = ['main.py','schemes_db.py','static/index.html','tests/test_dhvaani.py','build_phase2.py']
print("FILE INVENTORY AUDIT")
print("="*90)
for f in files:
    p = os.path.join(base, f)
    if os.path.exists(p):
        sz = os.path.getsize(p)
        mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{f:42s}  {sz:>8} bytes  sha256={sha(p)}  mtime={mt}")
    else:
        print(f"{f}  NOT FOUND")
print()
