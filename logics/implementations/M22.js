function execute(d, s) {
  const fn = function(d, s) {
      function pearson(v1, v2) {
        const m1 = v1.reduce((a, b) => a + b, 0) / v1.length;
        const m2 = v2.reduce((a, b) => a + b, 0) / v2.length;
        const num = v1.reduce((a, val, i) => a + (val - m1) * (v2[i] - m2), 0);
        const d1 = Math.sqrt(v1.reduce((a, val) => a + Math.pow(val - m1, 2), 0));
        const d2 = Math.sqrt(v2.reduce((a, val) => a + Math.pow(val - m2, 2), 0));
        return num / (d1 * d2 + 1e-10);
      }
      const dm = Math.sqrt(d.min.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dd = Math.sqrt(d.mid.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dx = Math.sqrt(d.max.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      const predInterp = (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
      
      const rMin = Math.max(0, pearson(s, d.min));
      const rMid = Math.max(0, pearson(s, d.mid));
      const rMax = Math.max(0, pearson(s, d.max));
      const totR = rMin + rMid + rMax + 1e-10;
      const predReg = (rMin * d.vals[0] + rMid * d.vals[1] + rMax * d.vals[2]) / totR;
      
      const minD = Math.min(dm, dd, dx);
      const conf = 1 / (1 + minD);
      return (1 - conf) * predReg + conf * predInterp;
    };
  return fn(d, s);
}
module.exports = execute;