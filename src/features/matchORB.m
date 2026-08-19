function result = matchORB(orb1, orb2, matchConfig)
%MATCHORB Match two sets of binary ORB descriptors.

arguments
    orb1 struct
    orb2 struct
    matchConfig struct
end

requiredORBFields = ["features", "validPoints"];
if any(~isfield(orb1, requiredORBFields)) || ...
        any(~isfield(orb2, requiredORBFields))
    error("myresearch:InvalidORBResult", ...
        "ORB inputs must contain features and validPoints fields.");
end

requiredConfigFields = ["method", "matchThreshold", "maxRatio", "unique"];
missingFields = requiredConfigFields(~isfield(matchConfig, requiredConfigFields));
if ~isempty(missingFields)
    error("myresearch:InvalidMatchConfig", ...
        "Missing matching configuration fields: %s", ...
        strjoin(missingFields, ", "));
end

validateattributes(matchConfig.matchThreshold, {'numeric'}, ...
    {'scalar', '>', 0, '<=', 100}, mfilename, ...
    "matchConfig.matchThreshold");
validateattributes(matchConfig.maxRatio, {'numeric'}, ...
    {'scalar', '>', 0, '<=', 1}, mfilename, "matchConfig.maxRatio");

timer = tic;
[indexPairs, matchMetric] = matchFeatures( ...
    orb1.features, orb2.features, ...
    Method=matchConfig.method, ...
    MatchThreshold=matchConfig.matchThreshold, ...
    MaxRatio=matchConfig.maxRatio, ...
    Unique=matchConfig.unique);
elapsedMs = toc(timer) * 1000;

matchedPoints1 = orb1.validPoints(indexPairs(:, 1));
matchedPoints2 = orb2.validPoints(indexPairs(:, 2));

result = struct;
result.indexPairs = indexPairs;
result.matchMetric = matchMetric;
result.matchedPoints1 = matchedPoints1;
result.matchedPoints2 = matchedPoints2;
result.count = size(indexPairs, 1);
result.elapsedMs = elapsedMs;

if isempty(matchMetric)
    result.meanMetric = NaN;
    result.medianMetric = NaN;
else
    result.meanMetric = mean(double(matchMetric));
    result.medianMetric = median(double(matchMetric));
end
end
