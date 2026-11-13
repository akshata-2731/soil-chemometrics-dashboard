function execute(d, s) {
  const fn = function(d, s) {
      function sc(vec) {
        const num = vec.reduce((a, val, i) => a + i * val, 0);
        const den = vec.reduce((a, val) => a + val, 0) + 1e-10;
        return num / den;
      }
      const cS = sc(s);
      const cMin = sc(d.min);
      const cMax = sc(d.max);
      const denom = Math.abs(cMax - cMin) > 1e-10 ? (cMax - cMin) : 1e-10;
      const t = clamp((cS - cMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;