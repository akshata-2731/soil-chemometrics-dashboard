function execute(d, s) {
  const fn = function(d, s) {
      const scaleS = Math.max(...s.map(Math.abs)) + 1e-10;
      const scaleMin = Math.max(...d.min.map(Math.abs)) + 1e-10;
      const scaleMid = Math.max(...d.mid.map(Math.abs)) + 1e-10;
      const scaleMax = Math.max(...d.max.map(Math.abs)) + 1e-10;
      
      const tS = s.map(x => Math.tanh(x / scaleS));
      const tMin = d.min.map(x => Math.tanh(x / scaleMin));
      const tMid = d.mid.map(x => Math.tanh(x / scaleMid));
      const tMax = d.max.map(x => Math.tanh(x / scaleMax));
      
      const dm = tS.reduce((a, v, i) => a + Math.abs(v - tMin[i]), 0);
      const dd = tS.reduce((a, v, i) => a + Math.abs(v - tMid[i]), 0);
      const dx = tS.reduce((a, v, i) => a + Math.abs(v - tMax[i]), 0);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(dm + eps, 2);
      const wd = 1 / Math.pow(dd + eps, 2);
      const wx = 1 / Math.pow(dx + eps, 2);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;