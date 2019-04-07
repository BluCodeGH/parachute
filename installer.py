import importlib
from io import BytesIO
import os
import sys
from colorama import init, Fore, Style
from dulwich import porcelain
init(autoreset=True)

if getattr(sys, "frozen", False) or "--clone" in sys.argv: # we are frozen, use the cloned version.
  # the main program should be cloned into the 'parachute' folder.
  if not os.path.isdir("parachute"):
    print(Fore.YELLOW + "! " + Style.RESET_ALL + "Couldn't detect existing parachute install. Installing...")
    porcelain.clone("https://github.com/BluCodeGH/parachute.git", "parachute")
    print(Fore.BLUE + "! "+ Style.RESET_ALL + "Installed.")
  else:
    print(Fore.BLUE + "! " + Style.RESET_ALL + "Updating parachute...")
    output = BytesIO()
    porcelain.pull("parachute", "https://github.com/BluCodeGH/parachute.git", errstream=output)
    if output.getvalue().decode()[:7] == "Total 0":
      print("  Already up to date.")
    else:
      print("  Update successful.")

  # Setup to run
  os.chdir("parachute")

else: # not frozen, so use the live parachute
  print(Fore.YELLOW + "! " + Style.RESET_ALL + "Detected live parachute install.")

# Actually run parachute
importlib.import_module("parachute")
