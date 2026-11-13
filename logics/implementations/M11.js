function execute(d, s) {
  const fn = function(d, s) {
      function getCR(vec) {
        const num = (vec[18] || 0) + (vec[19] || 0) + (vec[20] || 0);
        const den = (vec[6] || 0) + (vec[7] || 0) + 1e-10;
        return num / den;
      }
      const crS = getCR(s);
      const crMin = getCR(d.min);
      const crMax = getCR(d.max);
      const denom = Math.abs(crMax - crMin) > 1e-10 ? (crMax - crMin) : 1e-10;
      const t = clamp((crS - crMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;