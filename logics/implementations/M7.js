function execute(d, s) {
  const fn = function(d, s) {
      const v = d.mid.map((val, i) => val - d.min[i]);
      const sVec = s.map((val, i) => val - d.min[i]);
      const dotSV = sVec.reduce((a, val, i) => a + val * v[i], 0);
      const dotVV = v.reduce((a, val) => a + val * val, 0) + 1e-10;
      const alpha = clamp(dotSV / dotVV, 0, 1);
      return d.vals[0] + alpha * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;