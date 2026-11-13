function execute(d, s) {
  const fn = function(d, s) {
      function getFp(vec) {
        const mx = Math.max(...vec.map(Math.abs)) + 1e-10;
        const norm = vec.map(x => x / mx);
        return (norm[0] * norm[1]) / ((norm[2] || 0) + 1e-10);
      }
      const fpS = getFp(s);
      const fpMin = getFp(d.min);
      const fpMid = getFp(d.mid);
      const fpMax = getFp(d.max);
      
      const dm = Math.abs(fpS - fpMin);
      const dd = Math.abs(fpS - fpMid);
      const dx = Math.abs(fpS - fpMax);
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;