function execute(d, s) {
  const fn = function(d, s) {
      const steps = 50;
      const ladder = [];
      for (let k = 0; k <= steps; k++) {
        const t = k / steps;
        const valK = d.vals[0] + t * (d.vals[2] - d.vals[0]);
        let distSq = 0;
        for (let i = 0; i < s.length; i++) {
          const specK = d.min[i] + t * (d.max[i] - d.min[i]);
          distSq += Math.pow(s[i] - specK, 2);
        }
        ladder.push({ dist: Math.sqrt(distSq), val: valK });
      }
      ladder.sort((a, b) => a.dist - b.dist);
      const top3 = ladder.slice(0, 3);
      const eps = 1e-10;
      const wTotal = top3.reduce((a, item) => a + 1 / (item.dist + eps), 0);
      return top3.reduce((a, item) => a + (1 / (item.dist + eps)) * item.val, 0) / wTotal;
    };
  return fn(d, s);
}
module.exports = execute;