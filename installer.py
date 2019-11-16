from io import BytesIO
import os
from os.path import join, isdir
from shutil import which
import subprocess
import sys
import webbrowser
from colorama import init, Fore, Style
from dulwich import porcelain
init()

def info(*msg):
  print(Fore.BLUE + "! " + Style.RESET_ALL, end="")
  print(*msg)

def warn(*msg):
  print(Fore.YELLOW + "! " + Style.RESET_ALL, end="")
  print(*msg)

def err(*msg):
  print(Fore.RED + "! " + Style.RESET_ALL, end="")
  print(*msg)

python = None
for executable in ["python3", "python", "py"]:
  if which(executable):
    python = executable
    break
if not python:
  err("Python must be installed on your system.")
  webbrowser.open("https://www.python.org/downloads/")
  input("Press enter to quit.")
  sys.exit(1)

update = False
if getattr(sys, "frozen", False) or "--clone" in sys.argv: # we are frozen, use the cloned version.
  # the main program should be cloned into the 'parachute' folder.
  if not isdir("parachute"):
    update = True
    warn("Couldn't detect existing parachute install. Installing...")
    porcelain.clone("https://github.com/BluCodeGH/parachute.git", "parachute", errstream=BytesIO())
    print(Fore.BLUE + "! "+ Style.RESET_ALL + "Installed.")
  else:
    info("Updating parachute...")
    output = BytesIO()
    porcelain.pull("parachute", "https://github.com/BluCodeGH/parachute.git", errstream=output)
    if output.getvalue().decode()[:7] == "Total 0":
      print("  Already up to date.")
    else:
      update = True
      print("  Update successful.")

  # Setup to run
  os.chdir("parachute")
  sys.path.append(os.getcwd())

else: # not frozen, so use the live parachute
  info("Detected live parachute install.")

if not isdir("venv"):
  update = True
  warn("Creating virtualenv.")
  res = subprocess.run([python, "-m", "venv", "venv"], check=False, stderr=subprocess.PIPE, text=True)
  if res.returncode != 0:
    err("Could not create a virtualenv:", res.stderr)
    sys.exit(1)
  with open(join("venv", "pip.conf"), "w") as f:
    f.write("[install]\nuser = false")

try:
  old_os_path = os.environ.get("PATH", "")
  os.environ["PATH"] = join(os.getcwd(), "venv", "bin") + os.pathsep + old_os_path

  if update:
    warn("Updating dependencies...")
    res = subprocess.run(["pip", "install", "-r", "requirements.txt"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False)
    if res.returncode != 0:
      err("Error updating dependencies:", res.stderr)

  info("Running parachute.")
  subprocess.run(["python", "parachute.py"], stdout=sys.stdout, stderr=sys.stderr, check=False)
finally:
  os.environ["PATH"] = old_os_path
