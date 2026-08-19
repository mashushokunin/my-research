function config = experiment_config()
%EXPERIMENT_CONFIG Return shared settings for MATLAB experiments.
%
% Edit this function when changing dataset paths or experiment parameters.
% Keep the values fixed while comparing sharing methods.

configFile = string(mfilename("fullpath"));
matlabConfigDir = string(fileparts(configFile));
configDir = string(fileparts(matlabConfigDir));
projectRoot = string(fileparts(configDir));

config.projectRoot = projectRoot;
config.randomSeed = 42;

% Input pair for the first local baseline. These extracted frames are not
% tracked by Git, so MATLAB Online can use the built-in fallback below.
config.input.image1 = fullfile(projectRoot, "data", "interim", ...
    "frames_10fps", "structured", "IMG_5978", "frame_000000.jpg");
config.input.image2 = fullfile(projectRoot, "data", "interim", ...
    "frames_10fps", "structured", "IMG_5978", "frame_000005.jpg");
config.input.allowBuiltInFallback = true;
config.input.fallbackImage1 = "viprectification_deskLeft.png";
config.input.fallbackImage2 = "viprectification_deskRight.png";

% ORB settings. detectORBFeatures supports ScaleFactor and NumLevels;
% selectStrongest limits the number of points after detection.
config.orb.maxPoints = 1000;
config.orb.scaleFactor = 1.2;
config.orb.numLevels = 8;

% Matching settings for binary ORB descriptors.
config.match.method = "Exhaustive";
config.match.matchThreshold = 40;
config.match.maxRatio = 0.70;
config.match.unique = true;

config.visualization.maxMatches = 100;
config.visualization.visible = "on";

config.output.directory = fullfile(projectRoot, "results", "matlab", ...
    "exp01_orb_baseline");
config.output.summaryFile = "summary.csv";
config.output.figureFile = "matches.png";
end
