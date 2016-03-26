#!/usr/bin/python
#Program for tracking information on files

import sqlite3
import os, sys
import hashlib
import argparse

AUTOUPDATE=True
verbosity=0
showmissing=1

conn = sqlite3.connect('/home/pretzel/workspace/fileinfo/finfo.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS ENTRIES (id integer PRIMARY KEY, node integer, base varchar, path varchar, md5 varchar, size integer, time integer, description varchar)')

class E:
  key=0
  node=1
  base=2
  path=3
  md5=4
  size=5
  time=6
  description=7

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

def jprint(lead,str):
  # :
  print(lead*' '+str)

def md5(fname):
  #http://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
  hash_md5 = hashlib.md5()
  with open(fname, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hash_md5.update(chunk)
  return hash_md5.hexdigest()

def niceexit(code=1):
  conn.commit()
  conn.close()
  sys.exit(code)

# def test(CWD):
  #   # print("Hi")
  #   for f in sorted(os.listdir("."),key=lambda s: s.lower()):
  #     print(col.GRN+f+col.BLN)
  #     fs=os.stat(f)
  #     # print("  Mode: "+str(fs.st_mode))
  #     jprint(2,"Path: "+CWD)
  #     jprint(2,"Base: "+f)
  #     jprint(2,"Node: "+str(fs.st_ino))
  #     jprint(2,"Size: "+str(fs.st_size))
  #     if os.path.isfile(f):
  #       jprint(2,"MD5: "+md5(f))

def printfile(f,d=""):
  f=os.path.abspath(f)
  isfile = os.path.isfile(f)
  if not d:
    if isfile:
      d=os.path.dirname(f)
    else:
      d='/'.join(f.split('/')[:-1])
  f=f.split('/')[-1]
  fs=os.stat(f)
  n=str(fs.st_ino)
  s=str(fs.st_size)
  t=str(fs.st_mtime)
  if isfile:
    m = md5(f)
  # print(fs)

  toupdate=False
  desc=""
  color=col.RED
  if isfile:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"' AND md5='"+m+"'")
  else:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"'")
  if res:
    color=col.GRN
    desc=res[7]
  else:
    res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"'")
    if res:
      desc=res[7]
      usql = "UPDATE ENTRIES SET node="+n+",base='"+f+"',path='"+d+"',md5='"+m+"', size="+s+",time="+t+",description='"+desc+"' WHERE path='"+d+"' AND base='"+f+"'"
    elif isfile:
      res = desql("SELECT * FROM ENTRIES WHERE node='"+n+"' AND md5='"+m+"'")
      if res:
        desc=res[7]
        usql = "UPDATE ENTRIES SET node="+n+",base='"+f+"',path='"+d+"',md5='"+m+"', size="+s+",time="+t+",description='"+desc+"' WHERE node='"+n+"' AND md5='"+m+"'"
    if res:
      toupdate=True
      color=col.YLW

  if res or showmissing:
    print(color+f+col.BLN)

  if desc:
    jprint(2,col.CYN+desc+col.BLN)

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
    elif verbosity > 0:
      jprint(2,"Size: "+s)
    if res and t != str(res[E.time]):
      jprint(2,col.YLW+"Time: " + str(res[E.time]) + " -> " + t+col.BLN)
    elif verbosity > 0:
      jprint(2,"Time: "+t)
    if isfile:
      if res and m != res[E.md5]:
        jprint(3,col.YLW+"MD5: " + res[E.md5] + " -> " + m+col.BLN)
      elif verbosity > 0:
        jprint(3,"MD5: "+m)

  if AUTOUPDATE and toupdate:
    desql(usql)

def printdir(d):
  for f in sorted(os.listdir(d),key=lambda s: s.lower()):
    printfile(f,d)

#Debug execute SQL
def desql(sql):
  # print(col.MGN+sql+col.BLN)
  c.execute(sql)
  return c.fetchone()

#Debug print
def dprint(s):
  pass
  # print(s)

def addentry(f,d):
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
  print(f+": "+col.YLW+d+col.BLN)
  fs=os.stat(f)
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
      print("An entry already exists for " + col.WHT + res[3]+"/"+res[2] + ": " + col.CYN + res[7] + col.BLN)
      prompt="Overwrite (y) or cancel (n)? "
    elif exists == 2:
      print("A similar entry exists for " + col.WHT + res[3]+"/"+res[2] + ": " + col.CYN + res[7] + col.BLN)
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

def fixscan(sql,n,f,d,m,s,t):
  res = desql(sql)
  while res:
    if os.path.exists(res[E.path]+"/"+res[E.base]):
      res=c.fetchone() #Not an orphan, so continue
      continue
    jprint(2,str(res))
    print("Orphan found for " + col.YLW + res[E.path]+"/"+res[E.base]+"\n  "+col.CYN + res[E.description]+col.BLN)
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

def removescan(sql):
  res = desql(sql)
  while res:
    jprint(2,str(res))
    print("Entry found for " + col.YLW + res[E.path]+"/"+res[E.base]+"\n  "+col.CYN + res[E.description]+col.BLN)
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

def removeentry(f):
  f=os.path.abspath(f)
  isfile = os.path.isfile(f)
  if isfile:
    d=os.path.dirname(os.path.abspath(f))
    f=f.split('/')[-1]
  else:
    d='/'.join(os.path.abspath(f).split('/')[:-1])

  f=f.split('/')[-1]
  d=os.path.dirname(os.path.abspath(f))

  removescan("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"'")
  niceexit()

def fixentry(f):
  if not os.path.exists(f):
    print("File " + col.RED + f + col.BLN + " does not exist!")
    return
  f=f.split('/')[-1]
  d=os.path.dirname(os.path.abspath(f))
  fs=os.stat(f)
  isfile = os.path.isfile(f)
  n=str(fs.st_ino)
  s=str(fs.st_size)
  t=str(fs.st_mtime)
  if isfile:
    m = md5(f)

  res = desql("SELECT * FROM ENTRIES WHERE path='"+d+"' AND base='"+f+"' AND node='"+n+"' AND md5='"+m+"'")
  if res:
    print(col.RED+"File " + d+"/"+f + " is already in the database!"+col.BLN)
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

def printall(onlyorphans=False):
  res = desql("SELECT * FROM ENTRIES")
  while res:
    dprint(res)

    fpath=res[E.path]+"/"+res[E.base]
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
  # mode.add_argument("-c", "--clear",    help="clear the logfile",                  action="store_true")
  # parser.add_argument("-u", "--user",    type=str,   help="your Skype username", required=True)
  parser.add_argument("-f", "--fix", metavar='<filename>',  type=str,   help="find and fix a description among orphaned entries")
  parser.add_argument("-d", "--description", metavar='<description>', type=str,   help="add descriptions for listed files")
  parser.add_argument("-o", "--orphans", help="print orphaned entries", action="store_true")
  parser.add_argument("-a", "--all", help="print all entries", action="store_true")
  verb.add_argument("-v", "--verbose", help="print extra information", action="store_true")
  verb.add_argument("-q", "--quiet", help="print minimal information", action="store_true")
  parser.add_argument("-r", "--remove", help="remove the descriptions for the listed files", action="store_true")
  parser.add_argument("-e", "--existing", help="print only files with entries", action="store_true")
  parser.add_argument('files', metavar='F', type=str, nargs='*',help='Files to describe')
  return parser

def main():
  global verbosity, showmissing
  parser = configParser()
  args = parser.parse_args()
  anyargs=False
  #Parse other arguments
  if args.verbose:
    verbosity=1
  elif args.quiet:
    verbosity=-1
  if args.existing:
    showmissing=0
  if args.fix:
    fixentry(args.fix)
    niceexit()
  if args.orphans:
    # printall()
    printall(True)
    niceexit()
  if args.all:
    printall(False)
    niceexit()
  if args.description:
    for f in args.files:
      addentry(f,args.description)
    niceexit()
  if len(args.files) == 0 and not anyargs:
    printdir(os.getcwd())
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
