function execute(d, s) {
  const fn = function(d, s) {
      function grad(vec) {
        const g = [];
        for (let i = 0; i < vec.length - 1; i++) g.push(vec[i+1] - vec[i]);
        return g;
      }
      const gS = grad(s);
      const gMin = grad(d.min);
      const gMid = grad(d.mid);
      const gMax = grad(d.max);
      
      const dm = Math.sqrt(gS.reduce((a, v, i) => a + Math.pow(v - gMin[i], 2), 0));
      const dd = Math.sqrt(gS.reduce((a, v, i) => a + Math.pow(v - gMid[i], 2), 0));
      const dx = Math.sqrt(gS.reduce((a, v, i) => a + Math.pow(v - gMax[i], 2), 0));
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;