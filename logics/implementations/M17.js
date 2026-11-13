function execute(d, s) {
  const fn = function(d, s) {
      function mrs(vec) {
        const r1 = vec[0] / ((vec[1] || 0) + 1e-10);
        const r2 = vec[1] / ((vec[2] || 0) + 1e-10);
        const r3 = vec[2] / ((vec[3] || 0) + 1e-10);
        return (r1 + r2 + r3) / 3;
      }
      const scS = mrs(s);
      const scMin = mrs(d.min);
      const scMid = mrs(d.mid);
      const scMax = mrs(d.max);
      
      const dm = Math.abs(scS - scMin);
      const dd = Math.abs(scS - scMid);
      const dx = Math.abs(scS - scMax);
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;