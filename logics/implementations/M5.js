function execute(d, s) {
  const fn = function(d, s) {
      let votesMin = 0, votesMid = 0, votesMax = 0;
      for (let i = 0; i < s.length; i++) {
        const dm = Math.abs(s[i] - d.min[i]);
        const dd = Math.abs(s[i] - d.mid[i]);
        const dx = Math.abs(s[i] - d.max[i]);
        const best = Math.min(dm, dd, dx);
        if (best === dm) votesMin++;
        else if (best === dd) votesMid++;
        else votesMax++;
      }
      const total = votesMin + votesMid + votesMax || 1;
      return (votesMin * d.vals[0] + votesMid * d.vals[1] + votesMax * d.vals[2]) / total;
    };
  return fn(d, s);
}
module.exports = execute;