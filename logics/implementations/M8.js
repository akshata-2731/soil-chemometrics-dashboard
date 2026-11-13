function execute(d, s) {
  const fn = function(d, s) {
      const spread = d.min.map((v, i) => Math.abs((d.max[i] || 0) - v) + 1e-10);
      const sumSpread = spread.reduce((a, b) => a + b, 0);
      const weights = spread.map(w => w / sumSpread);
      
      const v = d.mid.map((val, i) => val - d.min[i]);
      const sVec = s.map((val, i) => val - d.min[i]);
      
      const weightedSV = sVec.reduce((a, val, i) => a + weights[i] * val * v[i], 0);
      const weightedVV = v.reduce((a, val) => a + weights[i] * val * val, 0) + 1e-10;
      
      const alpha = clamp(weightedSV / weightedVV, 0, 1);
      if (alpha <= 1.0) {
        return d.vals[0] + alpha * (d.vals[1] - d.vals[0]);
      } else {
        const beta = clamp(alpha - 1.0, 0, 1);
        return d.vals[1] + beta * (d.vals[2] - d.vals[1]);
      }
    };
  return fn(d, s);
}
module.exports = execute;