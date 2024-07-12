Name:           task
Version:        3.0.0
Release:        2
Summary:        Taskwarrior - a command-line TODO list manager
License:        MIT
URL:            https://taskwarrior.org
Source0:        %{url}/download/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  rust >= 1.70
BuildRequires:  cargo >= 1.70
BuildRequires:  rust-std-static

BuildRequires:  libuuid-devel

Provides:       taskwarrior
Conflicts:      taskwarrior

%description
Taskwarrior is a command-line TODO list manager. It is flexible, fast,
efficient, unobtrusive, does its job then gets out of your way.

Taskwarrior scales to fit your workflow. Use it as a simple app that captures
tasks, shows you the list, and removes tasks from that list. Leverage its
capabilities though, and it becomes a sophisticated data query tool that can
help you stay organized, and get through your work.

%prep
%autosetup

%build

# https://git.sailfishos.org/mer-core/gecko-dev/blob/master/rpm/xulrunner-qt5.spec#L224
# When cross-compiling under SB2 rust needs to know what arch to emit
# when nothing is specified on the command line. That usually defaults
# to "whatever rust was built as" but in SB2 rust is accelerated and
# would produce x86 so this is how it knows differently. Not needed
# for native x86 builds
%ifarch %arm
export SB2_RUST_TARGET_TRIPLE=armv7-unknown-linux-gnueabihf
export CFLAGS_armv7_unknown_linux_gnueabihf=$CFLAGS
export CXXFLAGS_armv7_unknown_linux_gnueabihf=$CXXFLAGS
%endif
%ifarch aarch64
export SB2_RUST_TARGET_TRIPLE=aarch64-unknown-linux-gnu
export CFLAGS_aarch64_unknown_linux_gnu=$CFLAGS
export CXXFLAGS_aarch64_unknown_linux_gnu=$CXXFLAGS
%endif
%ifarch %ix86
export SB2_RUST_TARGET_TRIPLE=i686-unknown-linux-gnu
export CFLAGS_i686_unknown_linux_gnu=$CFLAGS
export CXXFLAGS_i686_unknown_linux_gnu=$CXXFLAGS
%endif

export CFLAGS="-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -Wformat -Wformat-security -fmessage-length=0"
export CXXFLAGS=$CFLAGS
# This avoids a malloc hang in sb2 gated calls to execvp/dup2/chdir
# during fork/exec. It has no effect outside sb2 so doesn't hurt
# native builds.
export SB2_RUST_EXECVP_SHIM="/usr/bin/env LD_PRELOAD=/usr/lib/libsb2/libsb2.so.1 /usr/bin/env"
export SB2_RUST_USE_REAL_EXECVP=Yes
export SB2_RUST_USE_REAL_FN=Yes
export SB2_RUST_NO_SPAWNVP=Yes

%ifnarch %ix86
export HOST_CC=host-cc
export HOST_CXX=host-cxx
export CC_i686_unknown_linux_gnu=$HOST_CC
export CXX_i686_unknown_linux_gnu=$HOST_CXX
%endif

# Set meego cross compilers
export PATH=/opt/cross/bin/:$PATH
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_LINKER=armv7hl-meego-linux-gnueabi-gcc
export CC_armv7_unknown_linux_gnueabihf=armv7hl-meego-linux-gnueabi-gcc
export CXX_armv7_unknown_linux_gnueabihf=armv7hl-meego-linux-gnueabi-g++
export AR_armv7_unknown_linux_gnueabihf=armv7hl-meego-linux-gnueabi-ar
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=aarch64-meego-linux-gnu-gcc
export CC_aarch64_unknown_linux_gnu=aarch64-meego-linux-gnu-gcc
export CXX_aarch64_unknown_linux_gnu=aarch64-meego-linux-gnu-g++
export AR_aarch64_unknown_linux_gnu=aarch64-meego-linux-gnu-ar

# Hack for cross linking against dbus
export PKG_CONFIG_ALLOW_CROSS_i686_unknown_linux_gnu=1
export PKG_CONFIG_ALLOW_CROSS_armv7_unknown_linux_gnueabihf=1
export PKG_CONFIG_ALLOW_CROSS_aarch64_unknown_linux_gnu=1

%if %{with lto}
export CARGO_PROFILE_RELEASE_LTO=thin
%endif

# Workaround a Scratchbox bug - /tmp/[...]/symbols.o not found
export TMPDIR=${TMPDIR:-$(realpath "%{_sourcedir}/../.tmp")}
mkdir -p $TMPDIR

%cmake -DTASK_RCDIR=share/%{name} \
       -DCMAKE_BUILD_TYPE=Release \
       -DRust_CARGO_TARGET=$SB2_RUST_TARGET_TRIPLE
%cmake_build

%install
%cmake_install

# Move shell completion stuff to the right place
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions/
install -Dpm0644 scripts/zsh/_%{name} %{buildroot}%{_datadir}/zsh/site-functions/_%{name}
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions/
install -Dpm0644 scripts/bash/%{name}.sh %{buildroot}%{_datadir}/bash-completion/completions/%{name}
mkdir -p %{buildroot}%{_datadir}/fish/completions/
install -Dpm0644 scripts/fish/%{name}.fish %{buildroot}%{_datadir}/fish/completions/%{name}.fish

# Fix perms and drop shebangs
# that's only docs and it's written in README about permissings
find scripts/ -type f -exec chmod -x {} ';'
find scripts/ -type f -exec sed -i -e '1{\@^#!.*@d}' {} ';'

rm -vrf %{buildroot}%{_datadir}/doc/%{name}/

%files
%license LICENSE
%doc doc/ref/%{name}-ref.pdf
%doc scripts/vim/ scripts/hooks/
%{_bindir}/%{name}
# We don't want to have refresh script there
%exclude %{_datadir}/%{name}/refresh
%{_datadir}/%{name}/
%{_mandir}/man1/%{name}.1*
%{_mandir}/man5/%{name}rc.5*
%{_mandir}/man5/%{name}-color.5*
%{_mandir}/man5/%{name}-sync.5*
%dir %{_datadir}/zsh/
%dir %{_datadir}/zsh/site-functions/
%{_datadir}/zsh/site-functions/_%{name}
%dir %{_datadir}/bash-completion/
%dir %{_datadir}/bash-completion/completions/
%{_datadir}/bash-completion/completions/%{name}
%dir %{_datadir}/fish/
%dir %{_datadir}/fish/completions/
%{_datadir}/fish/completions/%{name}.fish
