function execute(d, s) {
  const fn = function(d, s) {
      const dm = Math.sqrt(d.min.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dd = Math.sqrt(d.mid.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dx = Math.sqrt(d.max.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;