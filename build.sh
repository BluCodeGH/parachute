#!/bin/bash

pyinstaller installer.py -F --hidden-import parachute \
  --hidden-import numpy --hidden-import packaging.specifiers --hidden-import packaging.requirements
