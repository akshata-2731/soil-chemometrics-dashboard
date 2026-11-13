function execute(d, s) {
  const fn = function(d, s) {
      function getAvgRatio(vec) {
        const ratios = [];
        const eps = 1e-10;
        for (let i = 0; i < vec.length; i++) {
          if (i + 1 < vec.length) ratios.push(vec[i] / (vec[i+1] + eps));
          if (i + 2 < vec.length) ratios.push(vec[i] / (vec[i+2] + eps));
        }
        return ratios.reduce((a, b) => a + b, 0) / (ratios.length || 1);
      }
      const rS = getAvgRatio(s);
      const rMin = getAvgRatio(d.min);
      const rMid = getAvgRatio(d.mid);
      const rMax = getAvgRatio(d.max);
      
      const dm = Math.abs(rS - rMin);
      const dd = Math.abs(rS - rMid);
      const dx = Math.abs(rS - rMax);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(dm + eps, 2);
      const wd = 1 / Math.pow(dd + eps, 2);
      const wx = 1 / Math.pow(dx + eps, 2);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;