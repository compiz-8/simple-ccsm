#!/usr/bin/env python

import sys, os, glob
import subprocess
from stat import *
from distutils.core import setup
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data

INSTALLED_FILES = "installed_files"

class install (_install):

    def run (self):
        _install.run (self)
        outputs = self.get_outputs ()
        length = 0
        if self.root:
            length += len (self.root)
        if self.prefix:
            length += len (self.prefix)
        if length:
            for counter in range (len (outputs)):
                outputs[counter] = outputs[counter][length:]
        data = "\n".join (outputs)
        try:
            file = open (INSTALLED_FILES, "w")
        except:
            self.warn ("Could not write installed files list %s" % \
                       INSTALLED_FILES)
            return
        file.write (data)
        file.close ()

class install_data (_install_data):

    def run (self):
        def chmod_data_file (file):
            try:
                os.chmod (file, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)
            except:
                self.warn ("Could not chmod data file %s" % file)
        _install_data.run (self)
        map (chmod_data_file, self.get_outputs ())

class uninstall (_install):

    def run (self):
        try:
            file = open (INSTALLED_FILES, "r")
        except:
            self.warn ("Could not read installed files list %s" % \
                       INSTALLED_FILES)
            return
        files = file.readlines ()
        file.close ()
        prepend = ""
        if self.root:
            prepend += self.root
        if self.prefix:
            prepend += self.prefix
        if len (prepend):
            for counter in range (len (files)):
                files[counter] = prepend + files[counter].rstrip ()
        for file in files:
            print("Uninstalling %s" % file)
            try:
                os.unlink (file)
            except:
                self.warn ("Could not remove file %s" % file)

ops = ("install", "build", "sdist", "uninstall", "clean")

if len (sys.argv) < 2 or sys.argv[1] not in ops:
    print("Please specify operation : %s" % " | ".join (ops))
    raise SystemExit(1)

prefix = None
gtkver = "3.0"
enableDesktopEffects = False
if "--enableDesktopEffects" in sys.argv:
    enableDesktopEffects = True
    sys.argv.remove ("--enableDesktopEffects")
if len (sys.argv) > 2:
    i = 0
    for o in sys.argv:
        if o.startswith ("--prefix"):
            if o == "--prefix":
                if len (sys.argv) >= i:
                    prefix = sys.argv[i + 1]
                sys.argv.remove (prefix)
            elif o.startswith ("--prefix=") and len (o[9:]):
                prefix = o[9:]
            sys.argv.remove (o)
        i += 1
    i = 0
    for o in sys.argv:
        if o.startswith ("--with-gtk"):
            if o == "--with-gtk":
                if len (sys.argv) >= i:
                    gtkver = sys.argv[i + 1]
                sys.argv.remove (gtkver)
            elif o.startswith ("--with-gtk=") and len (o[11:]):
                gtkver = o[11:]
            sys.argv.remove (o)
        i += 1
if not prefix and "PREFIX" in os.environ:
    prefix = os.environ["PREFIX"]
if not prefix or not len (prefix):
    prefix = "/usr/local"

if sys.argv[1] in ("install", "uninstall") and len (prefix):
    sys.argv += ["--prefix", prefix]

version_file = open ("VERSION", "r")
version = version_file.read ().strip ()
if "=" in version:
    version = version.split ("=")[1]

f = open (os.path.join ("simple-ccsm.in"), "rt")
data = f.read ()
f.close ()
data = data.replace ("@prefix@", prefix)
data = data.replace ("@version@", version)
data = data.replace ("@gtkver@", gtkver)
data = data.replace ("@enable_desktop_effects@", str(enableDesktopEffects))
f = open (os.path.join ("simple-ccsm"), "wt")
f.write (data)
f.close ()

cmd = "intltool-merge -d -u po/ simple-ccsm.desktop.in simple-ccsm.desktop".split(" ")
proc = subprocess.Popen(cmd)
proc.wait()

cmd = "intltool-merge -x -u po/ simple-ccsm.appdata.xml.in simple-ccsm.appdata.xml".split(" ")
proc = subprocess.Popen(cmd)
proc.wait()

profile_files = os.listdir("profiles/")
profiles = []
for profile in profile_files:
    profiles.append('profiles/%s' % profile)

data_files = [
                ("share/applications", ["simple-ccsm.desktop"]),
                ("share/metainfo", ["simple-ccsm.appdata.xml"]),
                ("share/simple-ccsm", ["simple-ccsm.ui"]),
                ("share/simple-ccsm/profiles", profiles)
             ]

custom_images = []

global_icon_path = "share/icons/hicolor/"
local_icon_path = "share/simple-ccsm/icons/hicolor/"

for dir, subdirs, files in os.walk("images/"):
    if dir == "images/":
        for file in files:
            custom_images.append(dir + file)
    else:
        images = []
        global_images = []

        for file in files:
            if file.find(".svg") or file.find(".png"):
                file_path = "%s/%s" % (dir, file)
                # global image
                if file[:-4] == "simple-ccsm":
                    global_images.append(file_path)
                # local image
                else:
                    images.append(file_path)
        # local
        if len(images) > 0:
            data_files.append((local_icon_path + dir[7:], images))
        # global
        if len(global_images) > 0:
            data_files.append((global_icon_path + dir[7:], global_images))

data_files.append(("share/simple-ccsm/images", custom_images))

podir = os.path.join (os.path.realpath ("."), "po")
if os.path.isdir (podir):
    buildcmd = "msgfmt -o build/locale/%s/simple-ccsm.mo po/%s.po"
    mopath = "build/locale/%s/simple-ccsm.mo"
    destpath = "share/locale/%s/LC_MESSAGES"
    for name in os.listdir (podir):
        if name[-2:] == "po":
            name = name[:-3]
            if sys.argv[1] == "build" \
               or (sys.argv[1] == "install" and \
                   not os.path.exists (mopath % name)):
                if not os.path.isdir ("build/locale/" + name):
                    os.makedirs ("build/locale/" + name)
                os.system (buildcmd % (name, name))
            data_files.append ((destpath % name, [mopath % name]))

setup (
        name             = "simple-ccsm",
        version          = version,
        description      = "Simple CompizConfig Settings Manager",
        author           = "Patrick Niklaus",
        author_email     = "patrick.niklaus@student.kit.edu",
        url              = "https://gitlab.com/compiz/simple-ccsm",
        license          = "GPLv2+",
        data_files       = data_files,
        packages         = [],
        scripts          = ["simple-ccsm"],
        cmdclass         = {"uninstall" : uninstall,
                            "install" : install,
                            "install_data" : install_data}
     )

os.remove ("simple-ccsm")
if sys.argv[1] == "install":
    gtk_update_icon_cache = '''gtk-update-icon-cache -f -t %s/share/icons/hicolor''' % prefix
    root_specified = len (list (filter (lambda s: s.startswith ("--root"), sys.argv))) > 0
    if not root_specified:
        print("Updating Gtk icon cache.")
        os.system (gtk_update_icon_cache)
    else:
        print('''*** Icon cache not updated. After install, run this:
***     %s''' % gtk_update_icon_cache)
