function execute(d, s) {
  const fn = function(d, s) {
      function angle(v1, v2) {
        const dot = v1.reduce((a, val, i) => a + val * v2[i], 0);
        const norm1 = Math.sqrt(v1.reduce((a, val) => a + val * val, 0)) + 1e-10;
        const norm2 = Math.sqrt(v2.reduce((a, val) => a + val * val, 0)) + 1e-10;
        const cosTheta = clamp(dot / (norm1 * norm2), -1, 1);
        return Math.acos(cosTheta);
      }
      const thetaMin = angle(s, d.min);
      const thetaMid = angle(s, d.mid);
      const thetaMax = angle(s, d.max);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(thetaMin + eps, 1.5);
      const wd = 1 / Math.pow(thetaMid + eps, 1.5);
      const wx = 1 / Math.pow(thetaMax + eps, 1.5);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;