# Makefile

SHELL := sh -e

VERSION := $$(awk -F= '/X-KDE-PluginInfo-Version/ { print $$2 }' plasma/metadata.desktop)
DATE := $$(date +"%Y-%m-%d")

_VEROMIX_SHARED := $(DESTDIR)/usr/share/veromix

all: build

build:
	sh Messages.sh

install: install-plasmoid install-gtk

install-service:
	mkdir -p $(_VEROMIX_SHARED)
	cp -a dbus-service common $(_VEROMIX_SHARED)

	mkdir -p $(_VEROMIX_SHARED)/data
	cp -a data/icons data/presets $(_VEROMIX_SHARED)/data

	mkdir -p $(DESTDIR)/usr/share/dbus-1/services
	cp -a data/dbus-1/services/* $(DESTDIR)/usr/share/dbus-1/services

	mkdir -p $(DESTDIR)/usr/share/icons
	ln -s ../veromix/data/icons/veromix.png $(DESTDIR)/usr/share/icons/veromix.png

	mkdir -p $(DESTDIR)/usr/share/locale
	cp -a data/locale/* $(DESTDIR)/usr/share/locale
	-find $(DESTDIR)/usr/share/locale -name "*.po" | xargs rm -f

install-plasmoid: install-service
	mkdir -p $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid
	cp -a plasma/contents plasma/metadata.desktop $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid

	mkdir -p $(DESTDIR)/usr/share/kde4/services
	ln -s ../apps/plasma/plasmoids/veromix-plasmoid/metadata.desktop $(DESTDIR)/usr/share/kde4/services/plasma-widget-veromix.desktop
	ln -sf ../../../../../../../veromix/common $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid/contents/code/veromixcommon
	ln -sf ../../../../../../veromix/data/icons $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid/contents/icons
	ln -sf ../../../../../../locale $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid/contents/locale
	ln -sf ../../../../../veromix/dbus-service $(DESTDIR)/usr/share/kde4/apps/plasma/plasmoids/veromix-plasmoid/dbus-service

install-gtk: install-service
	mkdir -p $(_VEROMIX_SHARED)
	cp -a gtk $(_VEROMIX_SHARED)

	mkdir -p $(DESTDIR)/usr/share/applications
	cp -a data/applications/veromix.desktop $(DESTDIR)/usr/share/applications

plasma-pkg: clean build
	cd plasma && zip -r ../../tmp-veroimx.plasmoid .
	cd ..
	mv ../tmp-veroimx.plasmoid ../$(DATE)_$(VERSION)_veromix.plasmoid

local-gtk: clean build
	echo "#!/bin/sh\ngtk/main.py" > veromix.sh
	chmod a+x veromix.sh
	echo "REQUIREMENTS:\n- python3-dbus\n- python3-gi\n- pulseaudio\n- python-xdg (Optional)\n- ladspa-sdk, swh-plugins (Optional)\n\n" > README
	echo "Configuration:\nSome basic configuration options can be found in ~/.config/veromix/veromix.conf" >> README
	tar cfzv ../$(DATE)_$(VERSION)_veromix-gtk.tar.gz --exclude=.git --exclude=debian --exclude="Makefile" --exclude="Messages.sh" --exclude="plasma" --exclude="contrib" ../$(shell basename $(CURDIR))
	rm veromix.sh README

clean:
	-find . -name '*~' | xargs rm -f
	-find . -name '*.pyc' | xargs rm -f
	-find . -name '__pycache__' | xargs rm -rf
	-find data/locale -name "*.mo" | xargs rm -f

distclean: clean

dist: clean
	tar cfzv ../veromix_$(VERSION).orig.tar.gz --exclude=.git --exclude=debian --exclude="contrib" ../$(shell basename $(CURDIR))
