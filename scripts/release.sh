#!/bin/sh

# Copyright (C) 2020  GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Usage:
#   $ env [DEV=yes] ./release.sh

set -e

IMAGE="${CI_PROJECT_NAME:-bmcmanager}"
BUILD="${CI_PIPELINE_IID:-none}"
SHA="${CI_COMMIT_SHORT_SHA:-none}"
DIR="${CI_PROJECT_DIR:-.}"
CONFIG_JSON="${CLOUDENG_SECRETS}/kaniko.config.json"

# Get version from CHANGELOG.md
if [ ! -z "${CI_COMMIT_TAG}" ]; then
    RELEASE="${CI_COMMIT_TAG}"
else
    RELEASE="$(sh ${DIR}/scripts/version.sh)"
fi
if [ -z "${RELEASE}" ]; then
    echo "Could not determine release version"
    exit 1
fi

# Tag release
if [ "x$DEVELOPMENT" = "xyes" ]; then
    REGISTRY="${REGISTRY_DEV}"
    VERSION="${RELEASE}-dev-${BUILD}-${SHA}"
    TAG="${REGISTRY}/${IMAGE}:${VERSION}"
    LATEST_TAG="${REGISTRY}/${IMAGE}:latest-dev"
else
    REGISTRY="${REGISTRY_PROD}"
    VERSION="${RELEASE}"
    TAG="${REGISTRY}/${IMAGE}:${VERSION}"
    LATEST_TAG="${REGISTRY}/${IMAGE}:latest"
fi

# Docker credentials
cp "${CONFIG_JSON}" "/kaniko/.docker/config.json"

/kaniko/executor \
    --context "${DIR}"                  \
    --dockerfile "${DIR}/Dockerfile"    \
    --destination "${TAG}"              \
    --destination "${LATEST_TAG}"

echo "Images published successfully:"
echo "  - ${TAG}"
echo "  - ${LATEST_TAG}"
