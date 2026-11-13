function execute(d, s) {
  const fn = function(d, s) {
      const sm = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.min[i]) + 1), 0);
      const sd = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.mid[i]) + 1), 0);
      const sx = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.max[i]) + 1), 0);
      const total = sm + sd + sx || 1;
      return (sm * d.vals[0] + sd * d.vals[1] + sx * d.vals[2]) / total;
    };
  return fn(d, s);
}
module.exports = execute;