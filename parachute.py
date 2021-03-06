import importlib
from io import BytesIO
import json
import os
from shutil import copyfile
import subprocess
import sys
import re
import readline
from colorama import init, Fore, Style
from dulwich import porcelain
init(autoreset=True)


def say(text, depth=0):
  print(depth * "  " + Fore.BLUE + "! " + Style.RESET_ALL + text)
def warn(text, depth=0):
  print(depth * "  " + Fore.YELLOW + "! " + Style.RESET_ALL + text)
def err(text, depth=0):
  print(depth * "  " + Fore.RED + "! " + Style.RESET_ALL + text)
def ask(q, depth=0):
  return input(depth * "  " + Fore.GREEN + "? " + Style.RESET_ALL + q)

# recursively apply fn across every submodule in a repo
def recurse(url, dest, fn):
  try:
    res = fn(url, dest)
  except Exception as e:
    print(e)
    return None
  try:
    with open(os.path.join(dest, ".gitmodules")) as submodules:
      lines = submodules.read().splitlines()
    sm = [None, None] # build url, path from multiple lines
    for line in lines:
      if line[0] == "[":
        if None not in sm and recurse(*sm, fn) is None:
          return None
        sm = [None, None]
      elif "path" in line:
        sm[1] = os.path.join(dest, line.split("=")[1].strip())
      elif "url" in line:
        sm[0] = line.split("=")[1].strip()
    if None not in sm and recurse(*sm, fn) is None:
      return None
  except FileNotFoundError:
    pass
  return res


try:
  with open("config.json") as iF:
    config = json.load(iF)
except FileNotFoundError:
  with open("config.json", "w") as oF:
    oF.write(json.dumps({"repos": []}, indent=2))
  config = {"repos": []}

if config["repos"]:
  say("Found installed programs: " + ", ".join([repo["name"] for repo in config["repos"]]))
  say("Checking for updates...")

  def pull(url, dest):
    res = BytesIO()
    porcelain.pull(dest, url, errstream=res)
    if res.getvalue().decode()[:7] != "Total 0":
      return True
    return False

  for repo in config["repos"]:
    output = recurse(repo["source"], repo["location"], pull)
    if output is None:
      err("Something went wrong updating " + repo["name"], 1)
    elif output:
      say(repo["name"], 1)
  say("Finished updating.")
else:
  say("No programs installed.")


reURL = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
reName = re.compile(r'.*/([^/]+)\.git$')

def install():
  source = ask("Please enter a source URL: ", 1)
  if not source.endswith(".git") or reURL.match(source) is None:
    err("Invalid source URL.", 1)
    return False
  name = reName.match(source).group(1)

  def clone(url, dest):
    porcelain.clone(url, dest, errstream=BytesIO())
    return True

  say("Downloading " + name, 1)
  if not recurse(source, name, clone):
    err("Something went wrong while installing " + name, 1)
    return False

  if module := os.path.isfile(os.path.join(name, "setup.py")):
    say("Installing " + name, 1)
    res = subprocess.run(["pip", "install", os.path.join(".", name)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if res.returncode != 0:
      err("Error installing module {}: {}".format(name, res.stderr), 1)
      return False

  if os.path.isfile(os.path.join(name, "requirements.txt")):
    say("Installing dependencies", 1)
    res = subprocess.run(["pip", "install", "-r", os.path.join(name, "requirements.txt")], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if res.returncode != 0:
      err("Error installing dependencies: {}".format(res.stderr), 1)
      return False

  os.makedirs(os.path.join("data", name), exist_ok=True)
  for f in os.listdir(name):
    if (f.endswith(".txt") and f != "requirements.txt") or f.endswith(".json"):
      copyfile(os.path.join(name, f), os.path.join("data", name, f))

  config["repos"].append({"source": source, "location": name, "name": name, "module": module})
  with open("config.json", "w") as oF:
    oF.write(json.dumps(config, indent=2))
  cmds.append(name)

  say("Installed. Run with `{}`".format(name), 1)
  return True


def run(cmd):
  name, *args = cmd.split()
  try:
    sys.path.append(os.path.join(os.getcwd(), name))
    sys.argv = ["parachute"] + args
    os.makedirs(os.path.join("data", name), exist_ok=True)
    os.chdir(os.path.join("data", name))
    if name not in modules:
      if [r["module"] for r in config["repos"] if r["name"] == name][0]:
        modules[name] = importlib.import_module("{}.__main__".format(name))
        print("imported")
      else:
        modules[name] = importlib.import_module(name)
    else:
      importlib.reload(modules[name])
  except Exception as e:
    warn("Something went wrong while running {}: {}".format(name, e), 1)
  except SystemExit as e:
    pass
  finally:
    sys.path.pop(-1)
    os.chdir(os.path.join("..", ".."))


cmds = ["help", "install", "quit"] + [repo["name"] for repo in config["repos"]]
readline.parse_and_bind("tab: complete")
readline.set_completer(lambda text, i: [cmd for cmd in cmds if cmd.startswith(text)][i])

modules = {}
print("Parachute loaded. Enter `help` for help.")
while True:
  try:
    cmd = input(Fore.BLUE + "> " + Style.RESET_ALL)
  except KeyboardInterrupt:
    print("Quitting!")
    break
  except EOFError:
    print("Quitting!")
    break

  if cmd.startswith("help"):
    print("""Parachute help:
help      - prints this message
install   - installs a program
quit      - quit parachute""")
  elif cmd.startswith("install"):
    install()
  elif cmd.startswith("quit") or cmd.startswith("exit"):
    break
  elif cmd.split()[0] in cmds: #an installed program
    run(cmd)
