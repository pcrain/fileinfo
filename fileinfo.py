#!/usr/bin/python
#Program for tracking information on files

import sqlite3, os, sys, hashlib, argparse

DEBUG=False
AUTOUPDATE=True  #Whether entries are automatically updated when viewed
verbosity=0       #Verbosity of output
showmissing=1     #Whether to show files without entries in listings

conn = sqlite3.connect(os.path.expanduser("~")+'/.finfo.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS ENTRIES (id integer PRIMARY KEY, node integer, base varchar, path varchar, md5 varchar, size integer, time integer, description varchar)')

#Class for enumerating table columns
class E:
  key=0
  node=1
  base=2
  path=3
  md5=4
  size=5
  time=6
  description=7

#Class for colors
class col:
  BLN      ='\033[0m'            # Blank
  UND      ='\033[1;4m'          # Underlined
  INV      ='\033[1;7m'          # Inverted
  CRT      ='\033[1;41m'         # Critical
  BLK      ='\033[1;30m'         # Black
  RED      ='\033[1;31m'         # Red
  GRN      ='\033[1;32m'         # Green
  YLW      ='\033[1;33m'         # Yellow
  BLU      ='\033[1;34m'         # Blue
  MGN      ='\033[1;35m'         # Magenta
  CYN      ='\033[1;36m'         # Cyan
  WHT      ='\033[1;37m'         # White

#Print with lead whitespace at the beginning
def jprint(lead,str):
  # :
  print(lead*' '+str)

#Compute md5sum for file
def md5(fname):
  #http://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
  hash_md5 = hashlib.md5()
  with open(fname, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hash_md5.update(chunk)
  return hash_md5.hexdigest()

#Commit changes to the database and exit
def niceexit(code=1):
  conn.commit()
  conn.close()
  sys.exit(code)

#Print the database entry (if any) matching the file in directory d
def printfile(of,d=""):
  lf=os.path.abspath(of)
  if not os.path.exists(lf):
    return
  f=os.path.realpath(lf)
  # print(f)

  islink = os.path.islink(lf)
  isfile = os.path.isfile(f)

  if isfile:
    d=os.path.dirname(f)
    if d != "/":
      d = d+"/"
    ld=os.path.dirname(lf)
    if ld != "/":
      ld = ld+"/"
  elif d != "/":
    d='/'.join(f.split('/')[:-1])+"/"
    ld='/'.join(lf.split('/')[:-1])+"/"

  f=f.split('/')[-1]
  lf=lf.split('/')[-1]

  if os.path.exists(f):
    fs=os.stat(f)
    n=str(fs.st_ino)
    s=str(fs.st_size)
    t=str(fs.st_mtime)
    if isfile:
      m = md5(f)
    else:
      m = ""
  else:
    fs=n=s=t=m=""

  lfs=os.lstat(lf)
  ln=str(lfs.st_ino)
  ls=str(lfs.st_size)
  lt=str(lfs.st_mtime)
  if isfile:
    lm = md5(lf)
  else:
    lm = ""

  # print(fs)

  toupdate=False
  desc=""
  color=col.RED

  found = False
  foundlink = False

  #First try to look for a file / direcotry with the exact same qualities
  res = desql("SELECT * FROM ENTRIES WHERE path='"+ld+"' AND base='"+lf+"' AND node='"+ln+"' AND md5='"+lm+"'")
  if res:
    color=col.GRN
    found = True
  #Follow any symlinks and check again for an exact match
  elif islink:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"' AND md5='"+m+"'")
    if res:
      color=col.MGN
      found = True
      foundlink = True
  if not found:
    #Find files with matching paths and basenames
    res = desql("SELECT * FROM ENTRIES WHERE path='"+ld+"' AND base='"+lf+"'")
    if res:
      desc=res[7]
      usql = "UPDATE ENTRIES SET node="+ln+",base='"+lf+"',path='"+ld+"',md5='"+lm+"', size="+ls+",time="+lt+",description='"+desc+"' WHERE path='"+ld+"' AND base='"+lf+"'"
    elif isfile:
      #Find files with matching inodes and md5sums
      res = desql("SELECT * FROM ENTRIES WHERE node='"+ln+"' AND md5='"+lm+"'")
      if res:
        desc=res[7]
        usql = "UPDATE ENTRIES SET node="+ln+",base='"+lf+"',path='"+ld+"',md5='"+lm+"', size="+ls+",time="+lt+",description='"+desc+"' WHERE node='"+ln+"' AND md5='"+lm+"'"
    else:
      #Find directories with matching inodes
      res = desql("SELECT * FROM ENTRIES WHERE node='"+ln+"'")
      if res:
        desc=res[7]
        usql = "UPDATE ENTRIES SET node="+ln+",base='"+lf+"',path='"+ld+"', size="+ls+",time="+lt+",description='"+desc+"' WHERE node='"+ln+"'"
    if res:
      toupdate=True
      color=col.YLW

  if res:
    desc=res[7]
    print(color+lf+col.BLN)
  elif showmissing:
    print(color+lf+col.BLN)

  if desc:
    jprint(2,col.CYN+desc+col.BLN)

  if not foundlink:
    d = ld
    f = lf
    n = ln
    s = ls
    t = lt
    m = lm

  if verbosity >= 0:
    if res and d != res[E.path]:
      jprint(2,col.YLW+"Path: " + res[E.path] + " -> " + d+col.BLN)
    elif verbosity > 0:
      jprint(2,"Path: "+d)
    if res and f != res[E.base]:
      jprint(2,col.YLW+"Base: " + res[E.base] + " -> " + f+col.BLN)
    elif verbosity > 0:
      jprint(2,"Base: "+f)
    if res and int(n) != res[E.node]:
      jprint(2,col.YLW+"Node: " + str(res[E.node]) + " -> " + n+col.BLN)
    elif verbosity > 0:
      jprint(2,"Node: "+n)
    if res and int(s) != res[E.size]:
      jprint(2,col.YLW+"Size: " + str(res[E.size]) + " -> " + s+col.BLN)
      desql("UPDATE ENTRIES SET size="+s+" WHERE id="+str(res[E.key]))
    elif verbosity > 0:
      jprint(2,"Size: "+s)
    if verbosity > 0 and res and t != str(res[E.time]):
      jprint(2,col.YLW+"Time: " + str(res[E.time]) + " -> " + t+col.BLN)
    elif verbosity > 0:
      jprint(2,"Time: "+t)
    if isfile:
      if res and m != res[E.md5]:
        jprint(2,col.YLW+"MD5: " + res[E.md5] + " -> " + m+col.BLN)
      elif verbosity > 0:
        jprint(2,"MD5: "+m)

  if AUTOUPDATE and toupdate:
    desql(usql)

#Debug execute SQL
def desql(sql):
  if DEBUG: print(col.MGN+sql+col.BLN)
  c.execute(sql)
  res=c.fetchone()
  if DEBUG and res:
    print(col.BLU+str(res)+col.BLN)
  return res

#Debug print
def dprint(s):
  pass
  # print(s)

#Add an entry to the database
def addentry(f,d):
  d=d.replace("'", "''")
  isfile = False
  m=""
  if os.path.isfile(f):
    isfile = True
    m=md5(f)
  elif not os.path.isdir(f):
    print("File " + f + " does not exist")
    niceexit()

  fname=os.path.abspath(f).split('/')[-1]
  curdir=os.path.dirname(os.path.abspath(f))
  if curdir != "/":
    curdir = curdir+"/"
  print(f+": "+col.YLW+d+col.BLN)
  fs=os.lstat(f)
  n=str(fs.st_ino)
  s=str(fs.st_size)
  t=str(fs.st_mtime)

  #Check if the file is already in the database
  exists=0
  res = desql("SELECT * FROM ENTRIES WHERE path='"+curdir+"' AND base='"+fname+"'")
  if res:
    exists=1
    dprint(res)
  else:
    if isfile:
      res = desql("SELECT * FROM ENTRIES WHERE node='"+n+"' AND md5='"+m+"'")
    else:
      res = desql("SELECT * FROM ENTRIES WHERE node='"+n+"'")
    if res:
      exists=2
      dprint(res)
  if exists > 0:
    if exists == 1:
      print("An entry already exists for " + col.WHT + res[3]+res[2] + ": " + col.CYN + res[7] + col.BLN)
      prompt="Overwrite (y) or cancel (n)? "
    elif exists == 2:
      print("A similar entry exists for " + col.WHT + res[3]+res[2] + ": " + col.CYN + res[7] + col.BLN)
      prompt="Overwrite (y) or add new (n)? "
    while True:
      inp = input(prompt)
      if inp == "n":
        if exists == 2:
          desql("INSERT INTO ENTRIES VALUES(NULL,"+n+",'"+fname+"','"+curdir+"','"+m+"',"+s+","+t+",'"+d+"')")
        niceexit()
      elif inp == "y":
        if exists == 1:
          desql("UPDATE ENTRIES SET node="+n+",base='"+fname+"',path='"+curdir+"',md5='"+m+"', size="+s+",time="+t+",description='"+d+"' WHERE path='"+curdir+"' AND base='"+fname+"'")
        elif exists == 2:
          desql("UPDATE ENTRIES SET node="+n+",base='"+fname+"',path='"+curdir+"',md5='"+m+"', size="+s+",time="+t+",description='"+d+"' WHERE node='"+n+"' AND md5='"+m+"'")
        niceexit()
  else:
    desql("INSERT INTO ENTRIES VALUES(NULL,"+n+",'"+fname+"','"+curdir+"','"+m+"',"+s+","+t+",'"+d+"')")

#Scan through matches for entries to update / fix
def fixscan(sql,n,f,d,m,s,t):
  res = desql(sql)
  while res:
    if os.path.exists(res[E.path]+"/"+res[E.base]):
      res=c.fetchone() #Not an orphan, so continue
      continue
    jprint(2,str(res))
    print("Orphan found for " + col.YLW + res[E.path]+res[E.base]+"\n  "+col.CYN + res[E.description]+col.BLN)
    while True:
      inp = input("Reassign (y), skip (n), or quit (q)? ")
      if inp == "q":
        return true
      if inp == "n":
        break
      if inp == "y":
        desql("UPDATE ENTRIES SET node="+n+",base='"+f+"',path='"+d+"',md5='"+m+"', size="+s+",time="+t+" WHERE id="+str(res[E.key]))
        return True
    res=c.fetchone()
  return False

#Scan through matches for entries to remove
def removescan(sql):
  res = desql(sql)
  while res:
    # jprint(2,str(res))
    print("Entry found for " + col.YLW + res[E.path]+res[E.base]+"\n  "+col.CYN + res[E.description]+col.BLN)
    while True:
      inp = input("Delete (y), skip (n), or quit (q)? ")
      if inp == "q":
        niceexit()
      if inp == "n":
        break
      if inp == "y":
        desql("DELETE FROM ENTRIES WHERE id="+str(res[E.key]))
        break
    res=c.fetchone()

#Remove an entry from the database
def removeentry(f):
  f=os.path.abspath(f)
  isfile = os.path.isfile(f)
  if isfile:
    d=os.path.dirname(f)
    if d != "/":
      d = d+"/"
    f=f.split('/')[-1]
  else:
    d='/'.join(f.split('/')[:-1])+"/"
    f=f.split('/')[-1]
  removescan("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"'")
  niceexit()

#Update / fix an orphaned entry in the database
def fixentry(f):
  if not os.path.exists(f):
    print("File " + col.RED + f + col.BLN + " does not exist!")
    return

  f=os.path.abspath(f)
  fs=os.stat(f)
  isfile = os.path.isfile(f)
  if isfile:
    d=os.path.dirname(f)
    if d != "/":
      d = d+"/"
    f=f.split('/')[-1]
  else:
    d='/'.join(f.split('/')[:-1])+"/"
    f=f.split('/')[-1]

  isfile = os.path.isfile(f)
  n=str(fs.st_ino)
  s=str(fs.st_size)
  t=str(fs.st_mtime)
  m=""
  if isfile:
    m = md5(f)

  if isfile:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"' AND md5='"+m+"'")
  else:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"'")
  if res:
    print(col.RED+"File " + d+f + " is already in the database!"+col.BLN)
    return

  print(col.WHT+"Searching orphans with same basenames..."+col.BLN)
  if fixscan("SELECT * FROM ENTRIES WHERE base='"+f+"'",n,f,d,m,s,t):
    niceexit()

  if isfile:
    print(col.WHT+"Searching orphans with same md5sums..."+col.BLN)
    if fixscan("SELECT * FROM ENTRIES WHERE md5='"+m+"'",n,f,d,m,s,t):
      niceexit()

  print(col.RED+"No suitable orphan found"+col.BLN)
  niceexit()

#Print all entries in the database
def printall(onlyorphans=False):
  res = desql("SELECT * FROM ENTRIES")
  while res:
    dprint(res)
    # if res[E.path] != "/":
    #   fpath=res[E.path]+"/"+res[E.base]
    # else:
    fpath=res[E.path]+res[E.base]
    if os.path.exists(fpath):
      if not onlyorphans:
        print(col.GRN+fpath+col.BLN)
        jprint(2,col.CYN+res[E.description])
    else:
      print(col.RED+fpath+col.BLN)
      jprint(2,col.CYN+res[E.description])
    res=c.fetchone()

#Configure command line arguments for the parser
def configParser():
  parser = argparse.ArgumentParser("fileinfo")
  verb = parser.add_mutually_exclusive_group()
  parser.add_argument("-f", "--fix", metavar='<filename>',  type=str,   help="find and fix a description among orphaned entries")
  parser.add_argument("-d", "--description", metavar='<description>', type=str,   help="add descriptions for listed files")
  parser.add_argument("-o", "--orphans", help="print orphaned entries", action="store_true")
  parser.add_argument("-a", "--all", help="print all entries", action="store_true")
  verb.add_argument("-v", "--verbose", help="print extra information", action="store_true")
  verb.add_argument("-q", "--quiet", help="print minimal information", action="store_true")
  parser.add_argument("-r", "--remove", help="remove the descriptions for the listed files", action="store_true")
  parser.add_argument("-e", "--existing", help="print only files with entries", action="store_true")
  parser.add_argument("--debug", help="debugging SQL print", action="store_true")
  parser.add_argument('files', metavar='F', type=str, nargs='*',help='Files to describe')
  return parser

def main():
  global verbosity, showmissing, DEBUG
  parser = configParser()
  args = parser.parse_args()
  anyargs=False
  #Parse other arguments
  if args.debug:
    DEBUG=True
  if args.existing:
    showmissing=0
  if args.verbose:
    verbosity=1
    showmissing=1
  elif args.quiet:
    verbosity=-1
  if args.fix:
    fixentry(args.fix)
    niceexit()
  if args.orphans:
    printall(True)
    niceexit()
  if args.all:
    printall(False)
    niceexit()
  if args.description:
    if len(args.files) == 0:
      print(col.RED + "No files specified!" + col.BLN)
    else:
      for f in args.files:
        addentry(f,args.description)
    niceexit()
  if len(args.files) == 0 and not anyargs:
    for f in sorted(os.listdir(os.getcwd()),key=lambda s: s.lower()):
      printfile(f)
    niceexit()
  else:
    if args.remove:
      for f in args.files:
        removeentry(f)
    else:
      for f in args.files:
        printfile(f)
    niceexit()

if __name__ == "__main__":
  main()
