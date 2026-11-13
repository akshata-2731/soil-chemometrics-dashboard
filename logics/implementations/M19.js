function execute(d, s) {
  const fn = function(d, s) {
      function curv(vec) {
        return (vec[14] || 0) - 2 * (vec[16] || 0) + (vec[18] || 0);
      }
      const cS = curv(s);
      const cMin = curv(d.min);
      const cMax = curv(d.max);
      const denom = Math.abs(cMax - cMin) > 1e-10 ? (cMax - cMin) : 1e-10;
      const t = clamp((cS - cMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;