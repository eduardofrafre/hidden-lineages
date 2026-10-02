#!/bin/sh
# Build the ASAP command line (Puillandre et al. 2021) into tools/asap.
#
# The source is the MNHN C code of 2022-10-27 as packaged in iTaxoTools/ASAPy
# (GPL-3); the original Bitbucket repository needs a login. Two changes from that copy:
# - wrapio.h is replaced by an empty header. ASAPy uses it to send stdio through
#   Python; without it the code is the plain command line.
# - "x:" is added to the getopt string. The usage text documents -x for the seed but
#   the parser rejects it, so the permutation p-values were seeded from the clock.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
src=$root/tools/ASAPy
[ -d "$src" ] || git clone -q --depth 1 https://github.com/iTaxoTools/ASAPy.git "$src"
build=$root/tools/asap-build
rm -rf "$build" && mkdir -p "$build"
cd "$src/src/asap"
cp oldfns.c oldfns.h asap.c asap.h asap_common.c asap_core.c asap_core.h gdtosvg.c gdtosvg.h draw.c "$build"
cd "$build"
echo '/* stdio build: no Python redirection */' > wrapio.h
sed -i 's/"o:l:n:p:d:amuhr:b:"/"o:l:n:p:d:amuhr:b:x:"/' asap.c
gcc -O3 -o "$root/tools/asap" oldfns.c asap.c asap_common.c asap_core.c gdtosvg.c draw.c -lm
echo "built $root/tools/asap"
