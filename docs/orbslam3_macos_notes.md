# ORB-SLAM3 macOS Build Notes

## Environment

- Homebrew packages installed: `cmake`, `pkg-config`, `eigen`, `opencv`
- Pangolin C++ library source: `external-repos/Pangolin`
- ORB-SLAM3 source: `external-repos/ORB_SLAM3`

## Local Compatibility Changes

The local ORB-SLAM3 checkout needed small compatibility changes for current macOS tooling.

- CMake 4: add `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` when configuring old CMake projects.
- Eigen 5: remove old fixed Eigen version requirements in ORB-SLAM3, g2o, and Sophus CMake files.
- Eigen 5: build ORB-SLAM3 with C++14 instead of C++11.
- AppleClang: replace unavailable `stdint-gcc.h` with standard `stdint.h`.
- AppleClang: replace old `std::tr1` includes/usages in bundled g2o with standard C++ headers/types.
- macOS dynamic libraries: link `libDBoW2${CMAKE_SHARED_LIBRARY_SUFFIX}` and `libg2o${CMAKE_SHARED_LIBRARY_SUFFIX}` instead of hardcoded `.so`.
- Homebrew libraries: add `/opt/homebrew/lib` to link directories.
- `mono_tum`: viewer disabled to allow non-interactive command-line runs.

## Configure Commands Used

```bash
cmake -S Thirdparty/DBoW2 -B Thirdparty/DBoW2/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 '-DCMAKE_CXX_FLAGS=-I/opt/homebrew/include'
cmake --build Thirdparty/DBoW2/build -j4

cmake -S Thirdparty/g2o -B Thirdparty/g2o/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 '-DCMAKE_CXX_FLAGS=-I/opt/homebrew/include -I/opt/homebrew/include/eigen3'
cmake --build Thirdparty/g2o/build -j4

cmake -S Thirdparty/Sophus -B Thirdparty/Sophus/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 '-DCMAKE_CXX_FLAGS=-I/opt/homebrew/include -I/opt/homebrew/include/eigen3'
cmake --build Thirdparty/Sophus/build -j4

cmake -S external-repos/Pangolin -B external-repos/Pangolin/build -DCMAKE_BUILD_TYPE=Release
cmake --build external-repos/Pangolin/build -j4

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPangolin_DIR=/Users/otsukamashu/univ-research/external-repos/Pangolin/build '-DCMAKE_CXX_FLAGS=-I/opt/homebrew/include -I/opt/homebrew/include/eigen3'
cmake --build build -j4
```

## Current Limitation

The ORB-SLAM3 camera config currently uses approximate intrinsics:

`configs/orbslam3/iphone_vertical_1080x1920_approx.yaml`

Use this for workflow checks and rough success/failure screening only. Replace it with real calibration before reporting SLAM accuracy.
