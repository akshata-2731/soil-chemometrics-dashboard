function execute(d, s) {
  const fn = function(d, s) {
      const meanS = s.reduce((a, b) => a + b, 0) / s.length;
      const meanMin = d.min.reduce((a, b) => a + b, 0) / d.min.length;
      const meanMid = d.mid.reduce((a, b) => a + b, 0) / d.mid.length;
      const meanMax = d.max.reduce((a, b) => a + b, 0) / d.max.length;
      
      const normS = s.map(x => x / meanS);
      const normMin = d.min.map(x => x / meanMin);
      const normMid = d.mid.map(x => x / meanMid);
      const normMax = d.max.map(x => x / meanMax);
      
      const spread = normMin.map((v, i) => Math.abs(normMax[i] - v) + 1e-10);
      const sumSpread = spread.reduce((a, b) => a + b, 0);
      const weights = spread.map(w => w / sumSpread);
      
      const dm = Math.sqrt(normS.reduce((a, v, i) => a + weights[i] * Math.pow(v - normMin[i], 2), 0));
      const dd = Math.sqrt(normS.reduce((a, v, i) => a + weights[i] * Math.pow(v - normMid[i], 2), 0));
      const dx = Math.sqrt(normS.reduce((a, v, i) => a + weights[i] * Math.pow(v - normMax[i], 2), 0));
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    };
  return fn(d, s);
}
module.exports = execute;