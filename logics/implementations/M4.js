function execute(d, s) {
  const fn = function(d, s) {
      const spread = d.min.map((v, i) => Math.abs((d.max[i] || 0) - v) + 1e-10);
      const sumSpread = spread.reduce((a, b) => a + b, 0);
      const weights = spread.map(w => w / sumSpread);
      
      const idxS = s.reduce((a, v, i) => a + v * weights[i], 0);
      const idxMin = d.min.reduce((a, v, i) => a + v * weights[i], 0);
      const idxMax = d.max.reduce((a, v, i) => a + v * weights[i], 0);
      
      const denom = Math.abs(idxMax - idxMin) > 1e-10 ? (idxMax - idxMin) : 1e-10;
      const t = clamp((idxS - idxMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;