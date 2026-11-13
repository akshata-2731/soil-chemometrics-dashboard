function execute(d, s) {
  const fn = function(d, s) {
      const eS = s.reduce((a, b) => a + b, 0);
      const eMin = d.min.reduce((a, b) => a + b, 0);
      const eMax = d.max.reduce((a, b) => a + b, 0);
      const denom = Math.abs(eMax - eMin) > 1e-10 ? (eMax - eMin) : 1e-10;
      const t = clamp((eS - eMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;