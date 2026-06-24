#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
echo "Building RPM package v${VERSION}..."

if ! command -v rpmbuild &> /dev/null; then
    echo "rpmbuild not found. Install rpm-build package."
    exit 1
fi

mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cp packaging/rpm/pdfsigner.spec ~/rpmbuild/SPECS/
cp -r pdfsigner ~/rpmbuild/SOURCES/ 2>/dev/null || true

rpmbuild -bb ~/rpmbuild/SPECS/pdfsigner.spec --define "version ${VERSION}"

echo "RPM package built in ~/rpmbuild/RPMS/"
