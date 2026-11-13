function execute(d, s) {
  const fn = function(d, s) {
      function dr(vec) {
        return ((vec[2] || 0) + (vec[4] || 0) + (vec[7] || 0)) / ((vec[13] || 0) + 1e-10);
      }
      const drS = dr(s);
      const drMin = dr(d.min);
      const drMax = dr(d.max);
      const denom = Math.abs(drMax - drMin) > 1e-10 ? (drMax - drMin) : 1e-10;
      const t = clamp((drS - drMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;