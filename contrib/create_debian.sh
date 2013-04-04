#!/bin/sh
_TMPDIR="/tmp/veromix-debian"
_GIT="${_TMPDIR}/git"
_BUILD="${_TMPDIR}/build"
rm -rf "${_TMPDIR}"
mkdir -p "${_GIT}"
mkdir -p "${_BUILD}"

cd "${_GIT}"
git clone https://code.google.com/p/veromix-plasmoid/ veromix
cd veromix
echo "rm -rf contrib"
make dist
cp ${_GIT}/*.orig.tar.gz "${_BUILD}"
cd "${_BUILD}"
tar -xzf *.orig.tar.gz
cd "${_BUILD}/veromix"
cp -a "${_GIT}/veromix/debian" .
dpkg-buildpackage
cd "${_BUILD}"
lintian *.deb
exit 0
