function execute(d, s) {
  const fn = function(d, s) {
      const dm = Math.sqrt(d.min.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dd = Math.sqrt(d.mid.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dx = Math.sqrt(d.max.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      
      const pts = [[dm, d.vals[0]], [dd, d.vals[1]], [dx, d.vals[2]]];
      pts.sort((a, b) => a[0] - b[0]);
      
      const d1 = pts[0][0], v1 = pts[0][1];
      const d2 = pts[1][0], v2 = pts[1][1];
      const zLocal = (v1 * d2 + v2 * d1) / (d1 + d2 + 1e-10);
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      const zIdw = (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
      
      return 0.4 * zLocal + 0.6 * zIdw;
    };
  return fn(d, s);
}
module.exports = execute;