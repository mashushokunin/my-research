#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/univ-research}"
EXTERNAL_ROOT="${EXTERNAL_ROOT:-$WORKSPACE_ROOT/external-repos}"
ORB_SLAM3_REPO="${ORB_SLAM3_REPO:-https://github.com/UZ-SLAMLab/ORB_SLAM3.git}"
PANGOLIN_REPO="${PANGOLIN_REPO:-https://github.com/stevenlovegrove/Pangolin.git}"

echo "Installing Jetson runtime packages"
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  cmake \
  git \
  libboost-all-dev \
  libeigen3-dev \
  libglew-dev \
  libgtk-3-dev \
  libopencv-dev \
  libpython3-dev \
  libssl-dev \
  libusb-1.0-0-dev \
  pkg-config \
  python3-dev \
  python3-opencv \
  python3-pip \
  python3-venv

mkdir -p "$EXTERNAL_ROOT"

if [ ! -d "$EXTERNAL_ROOT/Pangolin/.git" ]; then
  git clone "$PANGOLIN_REPO" "$EXTERNAL_ROOT/Pangolin"
fi

cmake -S "$EXTERNAL_ROOT/Pangolin" -B "$EXTERNAL_ROOT/Pangolin/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$EXTERNAL_ROOT/Pangolin/build" --parallel "$(nproc)"

if [ ! -d "$EXTERNAL_ROOT/ORB_SLAM3/.git" ]; then
  git clone "$ORB_SLAM3_REPO" "$EXTERNAL_ROOT/ORB_SLAM3"
fi

if [ -f "$EXTERNAL_ROOT/ORB_SLAM3/build.sh" ]; then
  (
    cd "$EXTERNAL_ROOT/ORB_SLAM3"
    chmod +x build.sh
    ./build.sh
  )
else
  cmake -S "$EXTERNAL_ROOT/ORB_SLAM3" -B "$EXTERNAL_ROOT/ORB_SLAM3/build" -DCMAKE_BUILD_TYPE=Release
  cmake --build "$EXTERNAL_ROOT/ORB_SLAM3/build" --parallel "$(nproc)"
fi

if [ -f "$WORKSPACE_ROOT/my-research/apps/jetson/requirements-jetson.txt" ]; then
  python3 -m pip install --user -r "$WORKSPACE_ROOT/my-research/apps/jetson/requirements-jetson.txt"
fi

echo "Jetson install finished"
echo "ORB_SLAM3: $EXTERNAL_ROOT/ORB_SLAM3"
echo "Pangolin build: $EXTERNAL_ROOT/Pangolin/build"
