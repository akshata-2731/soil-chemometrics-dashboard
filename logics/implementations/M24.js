function execute(d, s) {
  const fn = function(d, s) {
      const meanS = s.reduce((a, b) => a + b, 0) / s.length;
      const meanMin = d.min.reduce((a, b) => a + b, 0) / d.min.length;
      const meanMid = d.mid.reduce((a, b) => a + b, 0) / d.mid.length;
      const meanMax = d.max.reduce((a, b) => a + b, 0) / d.max.length;
      
      const denom = Math.abs(meanMax - meanMin) > 1e-10 ? (meanMax - meanMin) : 1e-10;
      const pos = (meanS - meanMin) / denom;
      const midPos = (meanMid - meanMin) / denom;
      
      if (pos <= midPos) {
        const t = clamp(pos / (midPos + 1e-10), 0, 1);
        return d.vals[0] + t * (d.vals[1] - d.vals[0]);
      } else {
        const t = clamp((pos - midPos) / (1 - midPos + 1e-10), 0, 1);
        return d.vals[1] + t * (d.vals[2] - d.vals[1]);
      }
    };
  return fn(d, s);
}
module.exports = execute;