function result = extractORB(image, orbConfig)
%EXTRACTORB Detect ORB points and extract binary ORB descriptors.
%
% result = extractORB(image, orbConfig) converts an RGB image to grayscale,
% detects ORB keypoints, keeps at most orbConfig.maxPoints strongest points,
% and extracts ORB descriptors.

arguments
    image {mustBeNumericOrLogical}
    orbConfig struct
end

requiredFields = ["maxPoints", "scaleFactor", "numLevels"];
missingFields = requiredFields(~isfield(orbConfig, requiredFields));
if ~isempty(missingFields)
    error("myresearch:InvalidORBConfig", ...
        "Missing ORB configuration fields: %s", strjoin(missingFields, ", "));
end

validateattributes(orbConfig.maxPoints, {'numeric'}, ...
    {'scalar', 'integer', 'positive'}, mfilename, "orbConfig.maxPoints");
validateattributes(orbConfig.scaleFactor, {'numeric'}, ...
    {'scalar', '>', 1}, mfilename, "orbConfig.scaleFactor");
validateattributes(orbConfig.numLevels, {'numeric'}, ...
    {'scalar', 'integer', 'positive'}, mfilename, "orbConfig.numLevels");

grayImage = im2gray(image);

timer = tic;
detectedPoints = detectORBFeatures(grayImage, ...
    ScaleFactor=orbConfig.scaleFactor, ...
    NumLevels=orbConfig.numLevels);
detectedCount = detectedPoints.Count;

if detectedCount == 0
    error("myresearch:NoORBPoints", ...
        "No ORB keypoints were detected in the input image.");
end

selectedCount = min(detectedCount, orbConfig.maxPoints);
selectedPoints = selectStrongest(detectedPoints, selectedCount);
[features, validPoints] = extractFeatures(grayImage, selectedPoints, ...
    Method="ORB");
elapsedMs = toc(timer) * 1000;

if features.NumFeatures == 0
    error("myresearch:NoORBDescriptors", ...
        "ORB keypoints were detected, but no valid descriptors were extracted.");
end

result = struct;
result.grayImage = grayImage;
result.detectedPoints = detectedPoints;
result.selectedPoints = selectedPoints;
result.validPoints = validPoints;
result.features = features;
result.detectedCount = detectedCount;
result.selectedCount = selectedPoints.Count;
result.validCount = features.NumFeatures;
result.descriptorBits = features.NumBits;
result.descriptorBytes = numel(features.Features);
result.elapsedMs = elapsedMs;
end

function mustBeNumericOrLogical(value)
if ~(isnumeric(value) || islogical(value))
    error("myresearch:InvalidImageType", ...
        "Input image must be a numeric or logical array.");
end
end
