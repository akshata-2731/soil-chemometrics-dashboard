function execute(d, s) {
  const fn = function(d, s) {
      function gain(vec) {
        const r1 = (vec[18] || 0) / ((vec[10] || 0) + 1e-10);
        const r2 = (vec[14] || 0) / ((vec[9] || 0) + 1e-10);
        return Math.sqrt(Math.max(0, r1 * r2));
      }
      const gS = gain(s);
      const gMin = gain(d.min);
      const gMax = gain(d.max);
      const denom = Math.abs(gMax - gMin) > 1e-10 ? (gMax - gMin) : 1e-10;
      const t = clamp((gS - gMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    };
  return fn(d, s);
}
module.exports = execute;