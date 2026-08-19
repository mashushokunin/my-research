# Project Guidance

## Research direction

- This repository studies communication-efficient cooperative Visual SLAM under bandwidth constraints.
- The current research environment is Mac + MATLAB. MATLAB Online may also be used.
- Use MATLAB as the default language for new experiments and reusable research code.
- Use Simulink only when modeling bandwidth, delay, transmission intervals, or related communication behavior adds value.

## Repository conventions

- Put reusable MATLAB functions in the matching domain under `src/`.
- Put reproducible experiment entry points in `experiments/`.
- Put MATLAB experiment settings in `configs/matlab/`.
- Put Simulink models in `simulink/`.
- Keep MATLAB-generated `.prj` and `resources/project/` definition files in Git after project initialization.
- Keep large datasets and generated outputs out of Git according to `.gitignore`.
- Treat existing Python, Jupyter, Jetson, and ORB-SLAM3 files as previous research assets. Do not remove or rewrite them unless explicitly requested.

## Evaluation priorities

- Compare compressed images, all keypoints plus descriptors, and selected keypoints plus descriptors under consistent conditions.
- Record actual transmitted bytes, matching quality, relative-pose success, pose errors, and processing time.
- Keep the initial required scope at two-view relative-pose estimation; treat full SLAM metrics such as ATE and RPE as extensions.
