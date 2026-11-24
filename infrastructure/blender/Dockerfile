FROM ubuntu:24.04
ARG BLENDER_VERSION=4.5.17
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl xz-utils python3 libx11-6 libxi6 libxxf86vm1 libxfixes3 \
    libxrender1 libsm6 libice6 libgl1 libegl1 libgomp1 libxkbcommon0 \
    libwayland-client0 libwayland-cursor0 libwayland-egl1 libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*
RUN set -eux; \
    archive="blender-${BLENDER_VERSION}-linux-x64.tar.xz"; \
    url="https://mirror.blender.org/release/Blender4.5"; \
    cd /tmp; \
    curl -fSL --retry 2 --connect-timeout 20 --max-time 600 -o "$archive" "$url/$archive"; \
    curl -fSL --retry 2 --connect-timeout 20 --max-time 60 -o "blender-${BLENDER_VERSION}.sha256" "$url/blender-${BLENDER_VERSION}.sha256"; \
    awk -v name="$archive" '$2 == name || $2 == "*" name {print}' "blender-${BLENDER_VERSION}.sha256" > archive.sha256; \
    test -s archive.sha256; sha256sum -c archive.sha256; \
    mkdir -p /opt/blender; tar -xJf "$archive" --strip-components=1 -C /opt/blender; \
    rm "$archive" archive.sha256 "blender-${BLENDER_VERSION}.sha256"
ENV BLENDER_BIN=/opt/blender/blender
ENV HOME=/tmp
WORKDIR /work
ENTRYPOINT ["python3", "scripts/studio_render.py"]
