Name:           pdfsigner
Version:        1.0.0
Release:        1
Summary:        Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP

License:        AGPLv3
URL:            https://github.com/shurshick/pdf-signer-linux
BuildArch:      x86_64

%description
Self-contained desktop application for signing PDF documents with CryptoPro
CSP on Linux. Supports embedded CAdES-BES signatures via PKCS#11, visible
stamps compliant with GOST R 7.0.97-2025, signature verification, and
CryptoPro diagnostics. No Python installation required.

%prep
# Nothing to unpack - binary is pre-built.

%build
# Build is done by the external script.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
cp -f %{_sourcedir}/pdfsigner %{buildroot}/usr/bin/pdfsigner
chmod 755 %{buildroot}/usr/bin/pdfsigner

mkdir -p %{buildroot}/usr/share/applications
cp -f %{_sourcedir}/pdfsigner.desktop %{buildroot}/usr/share/applications/

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp -f %{_sourcedir}/pdfsigner.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/ 2>/dev/null || true

mkdir -p %{buildroot}/usr/share/doc/pdfsigner
cp -f %{_sourcedir}/README.md %{buildroot}/usr/share/doc/pdfsigner/ 2>/dev/null || true
cp -f %{_sourcedir}/LICENSE %{buildroot}/usr/share/doc/pdfsigner/COPYING 2>/dev/null || true

%files
/usr/bin/pdfsigner
/usr/share/applications/pdfsigner.desktop
/usr/share/icons/hicolor/256x256/apps/pdfsigner.png
/usr/share/doc/pdfsigner/

%changelog
* Sun Jun 23 2026 shurshick <noreply@example.com> - 1.0.0-1
- Initial release with self-contained binary, embedded PDF signing,
  GOST-compliant stamps, signature verification, and diagnostics.
