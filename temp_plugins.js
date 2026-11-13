module.exports = [
  {
    id: 1,
    name: 'Standard Euclidean + IDW',
    code: 'M1',
    targetNutrient: 'OC',
    targetNutrients: ['OC'],
    desc: 'Euclidean distance across spectrum with Inverse Distance Weighting (IDW p=1.0)',
    formula: 'd_i = ((S - C_i)), w_i = 1/(d_i + ), Pred = (w_i  V_i) / w_i',
    builtin: true,
    active: true,
    fn: function(d, s) {
      const dm = Math.sqrt(d.min.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dd = Math.sqrt(d.mid.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dx = Math.sqrt(d.max.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    }
  },
  {
    id: 2,
    name: 'Fingerprint Tanh + Manhattan',
    code: 'M2',
    targetNutrient: 'N',
    targetNutrients: ['N'],
    desc: 'Scale-normalized tanh transformation with Manhattan distance and IDW (p=2.0)',
    formula: 'T(x)=tanh(x/max|s|), d=|T(S)-T(C)|, w=1/(d+), Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const scaleS = Math.max(...s.map(Math.abs)) + 1e-10;
      const scaleMin = Math.max(...d.min.map(Math.abs)) + 1e-10;
      const scaleMid = Math.max(...d.mid.map(Math.abs)) + 1e-10;
      const scaleMax = Math.max(...d.max.map(Math.abs)) + 1e-10;
      
      const tS = s.map(x => Math.tanh(x / scaleS));
      const tMin = d.min.map(x => Math.tanh(x / scaleMin));
      const tMid = d.mid.map(x => Math.tanh(x / scaleMid));
      const tMax = d.max.map(x => Math.tanh(x / scaleMax));
      
      const dm = tS.reduce((a, v, i) => a + Math.abs(v - tMin[i]), 0);
      const dd = tS.reduce((a, v, i) => a + Math.abs(v - tMid[i]), 0);
      const dx = tS.reduce((a, v, i) => a + Math.abs(v - tMax[i]), 0);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(dm + eps, 2);
      const wd = 1 / Math.pow(dd + eps, 2);
      const wx = 1 / Math.pow(dx + eps, 2);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    }
  },
  {
    id: 3,
    name: 'KNN Ratio Fusion',
    code: 'M3',
    targetNutrient: 'P',
    targetNutrients: ['P'],
    desc: 'Pairwise adjacent band ratios (i+1, i+2) with mean ratio Manhattan distance & IDW (p=2.0)',
    formula: 'Ratio=S[i]/S[j], d=|Ratio_S - Ratio_C|, w=1/(d+), Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function getAvgRatio(vec) {
        const ratios = [];
        const eps = 1e-10;
        for (let i = 0; i < vec.length; i++) {
          if (i + 1 < vec.length) ratios.push(vec[i] / (vec[i+1] + eps));
          if (i + 2 < vec.length) ratios.push(vec[i] / (vec[i+2] + eps));
        }
        return ratios.reduce((a, b) => a + b, 0) / (ratios.length || 1);
      }
      const rS = getAvgRatio(s);
      const rMin = getAvgRatio(d.min);
      const rMid = getAvgRatio(d.mid);
      const rMax = getAvgRatio(d.max);
      
      const dm = Math.abs(rS - rMin);
      const dd = Math.abs(rS - rMid);
      const dx = Math.abs(rS - rMax);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(dm + eps, 2);
      const wd = 1 / Math.pow(dd + eps, 2);
      const wx = 1 / Math.pow(dx + eps, 2);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    }
  },
  {
    id: 4,
    name: 'Spectral Nutrient Index',
    code: 'M4',
    targetNutrient: 'K',
    targetNutrients: ['K'],
    desc: 'Spread-weighted spectral index with normalized linear interpolation between MIN & MAX',
    formula: 'W=|MAX-MIN|/spread, Index=(SW), t=(Idx_S - Idx_MIN)/(Idx_MAX - Idx_MIN), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const spread = d.min.map((v, i) => Math.abs((d.max[i] || 0) - v) + 1e-10);
      const sumSpread = spread.reduce((a, b) => a + b, 0);
      const weights = spread.map(w => w / sumSpread);
      
      const idxS = s.reduce((a, v, i) => a + v * weights[i], 0);
      const idxMin = d.min.reduce((a, v, i) => a + v * weights[i], 0);
      const idxMax = d.max.reduce((a, v, i) => a + v * weights[i], 0);
      
      const denom = Math.abs(idxMax - idxMin) > 1e-10 ? (idxMax - idxMin) : 1e-10;
      const t = clamp((idxS - idxMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 5,
    name: 'Spectral Voting Engine',
    code: 'M5',
    targetNutrient: 'K',
    targetNutrients: ['K'],
    desc: 'Per-wavelength nearest neighbor voting across reference points (MIN/MID/MAX)',
    formula: 'Vote=argmin(|S[i]-C_k[i]|), Pred = (Votes_minV_min + Votes_midV_mid + Votes_maxV_max) / Total',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 6,
    name: 'Unified Adaptive',
    code: 'M6',
    targetNutrient: 'Ca',
    targetNutrients: ['Ca'],
    desc: 'Ensemble blend of local 2-point interpolation (40%) and global IDW (60%)',
    formula: 'Pred = 0.4  z_local(2-nearest) + 0.6  z_idw(p=1.0)',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 7,
    name: 'Adaptive Projection',
    code: 'M7',
    targetNutrient: 'Ca',
    targetNutrients: ['Ca'],
    desc: 'Vector projection of sample onto calibration direction vector (MID - MIN)',
    formula: 'V=MID-MIN, S=Sample-MIN, =clamp((SV)/(VV), 0, 1), Pred=MIN + (MAX - MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const v = d.mid.map((val, i) => val - d.min[i]);
      const sVec = s.map((val, i) => val - d.min[i]);
      const dotSV = sVec.reduce((a, val, i) => a + val * v[i], 0);
      const dotVV = v.reduce((a, val) => a + val * val, 0) + 1e-10;
      const alpha = clamp(dotSV / dotVV, 0, 1);
      return d.vals[0] + alpha * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 8,
    name: 'Weighted Projection',
    code: 'M8',
    targetNutrient: 'Mg',
    targetNutrients: ['Mg'],
    desc: 'Spread-weighted vector projection onto MIN-MID-MAX piecewise segments',
    formula: 'W=spread/spread, =clamp((WSV)/(WV), 0, 1), Piecewise MINMIDMAX',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const spread = d.min.map((v, i) => Math.abs((d.max[i] || 0) - v) + 1e-10);
      const sumSpread = spread.reduce((a, b) => a + b, 0);
      const weights = spread.map(w => w / sumSpread);
      
      const v = d.mid.map((val, i) => val - d.min[i]);
      const sVec = s.map((val, i) => val - d.min[i]);
      
      const weightedSV = sVec.reduce((a, val, i) => a + weights[i] * val * v[i], 0);
      const weightedVV = v.reduce((a, val) => a + weights[i] * val * val, 0) + 1e-10;
      
      const alpha = clamp(weightedSV / weightedVV, 0, 1);
      if (alpha <= 1.0) {
        return d.vals[0] + alpha * (d.vals[1] - d.vals[0]);
      } else {
        const beta = clamp(alpha - 1.0, 0, 1);
        return d.vals[1] + beta * (d.vals[2] - d.vals[1]);
      }
    }
  },
  {
    id: 9,
    name: '10-Step Advanced',
    code: 'M9',
    targetNutrient: 'S',
    targetNutrients: ['S'],
    desc: 'Mean-ratio normalization, spread weighting, weighted Euclidean distance and IDW',
    formula: 'Norm=S/mean(S), W=spread/spread, d=((W(Norm_S - Norm_C))), IDW p=1.0',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 10,
    name: 'Dense Ladder',
    code: 'M10',
    targetNutrient: 'Fe',
    targetNutrients: ['Fe'],
    desc: '50-step synthetic spectra ladder along MIN-MAX trajectory with top-3 IDW interpolation',
    formula: '50 synthetic steps on MINMAX path, find top 3 nearest synthetic spectra, IDW p=1.0',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 11,
    name: 'Carbon Response Index',
    code: 'M11',
    targetNutrient: 'Mn',
    targetNutrients: ['Mn'],
    desc: 'Specific spectral ratio index (B18+B19+B20)/(B6+B7) with safe interpolation',
    formula: 'CRI = (B18+B19+B20)/(B6+B7), t=clamp((CRI_S - CRI_MIN)/(CRI_MAX - CRI_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function getCR(vec) {
        const num = (vec[18] || 0) + (vec[19] || 0) + (vec[20] || 0);
        const den = (vec[6] || 0) + (vec[7] || 0) + 1e-10;
        return num / den;
      }
      const crS = getCR(s);
      const crMin = getCR(d.min);
      const crMax = getCR(d.max);
      const denom = Math.abs(crMax - crMin) > 1e-10 ? (crMax - crMin) : 1e-10;
      const t = clamp((crS - crMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 12,
    name: 'Spectral Energy',
    code: 'M12',
    targetNutrient: 'Cu',
    targetNutrients: ['Cu'],
    desc: 'Total integrated spectral energy with normalized interpolation',
    formula: 'Energy = (spectrum), t=clamp((E_S - E_MIN)/(E_MAX - E_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const eS = s.reduce((a, b) => a + b, 0);
      const eMin = d.min.reduce((a, b) => a + b, 0);
      const eMax = d.max.reduce((a, b) => a + b, 0);
      const denom = Math.abs(eMax - eMin) > 1e-10 ? (eMax - eMin) : 1e-10;
      const t = clamp((eS - eMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 13,
    name: 'Projection Vector',
    code: 'M13',
    targetNutrient: 'Zn',
    targetNutrients: ['Zn'],
    desc: 'Directional spectral vector projection along MINMID calibration axis',
    formula: 'V=MID-MIN, S=Sample-MIN, =clamp((SV)/(VV), 0, 1), Pred=MIN + (MAX - MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const v = d.mid.map((val, i) => val - d.min[i]);
      const sVec = s.map((val, i) => val - d.min[i]);
      const dotSV = sVec.reduce((a, val, i) => a + val * v[i], 0);
      const dotVV = v.reduce((a, val) => a + val * val, 0) + 1e-10;
      const alpha = clamp(dotSV / dotVV, 0, 1);
      return d.vals[0] + alpha * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 14,
    name: 'Spectral Angle',
    code: 'M14',
    targetNutrient: 'B',
    targetNutrients: ['B'],
    desc: 'Spectral Angle Mapper (SAM) measuring angle  between spectral vectors, IDW (p=1.5)',
    formula: 'cos()=(AB)/(||A||||B||), =arccos(cos ), w=1/(+)^1.5, Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function angle(v1, v2) {
        const dot = v1.reduce((a, val, i) => a + val * v2[i], 0);
        const norm1 = Math.sqrt(v1.reduce((a, val) => a + val * val, 0)) + 1e-10;
        const norm2 = Math.sqrt(v2.reduce((a, val) => a + val * val, 0)) + 1e-10;
        const cosTheta = clamp(dot / (norm1 * norm2), -1, 1);
        return Math.acos(cosTheta);
      }
      const thetaMin = angle(s, d.min);
      const thetaMid = angle(s, d.mid);
      const thetaMax = angle(s, d.max);
      
      const eps = 1e-10;
      const wm = 1 / Math.pow(thetaMin + eps, 1.5);
      const wd = 1 / Math.pow(thetaMid + eps, 1.5);
      const wx = 1 / Math.pow(thetaMax + eps, 1.5);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    }
  },
  {
    id: 15,
    name: 'Spectral Gradient',
    code: 'M15',
    targetNutrient: 'OC',
    targetNutrients: ['OC'],
    desc: 'First derivative (spectral gradient s) with Euclidean distance and IDW (p=1.0)',
    formula: 'G[i]=S[i+1]-S[i], d=((G_S - G_C)), w=1/(d+), Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 16,
    name: 'Dynamic Ratio',
    code: 'M16',
    targetNutrient: 'OC',
    targetNutrients: ['OC'],
    desc: 'Multi-band combination index (B2+B4+B7)/B13 with safe interpolation',
    formula: 'DRI=(B2+B4+B7)/B13, t=clamp((DRI_S - DRI_MIN)/(DRI_MAX - DRI_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function dr(vec) {
        return ((vec[2] || 0) + (vec[4] || 0) + (vec[7] || 0)) / ((vec[13] || 0) + 1e-10);
      }
      const drS = dr(s);
      const drMin = dr(d.min);
      const drMax = dr(d.max);
      const denom = Math.abs(drMax - drMin) > 1e-10 ? (drMax - drMin) : 1e-10;
      const t = clamp((drS - drMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 17,
    name: 'Multi Ratio Sulphur',
    code: 'M17',
    targetNutrient: 'S',
    targetNutrients: ['S'],
    desc: 'Three-band adjacent ratio score (B0/B1 + B1/B2 + B2/B3)/3 with Manhattan IDW (p=1.0)',
    formula: 'Score=(B0/B1 + B1/B2 + B2/B3)/3, d=|Score_S - Score_C|, w=1/(d+), Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 18,
    name: 'Spectral Centroid',
    code: 'M18',
    targetNutrient: 'Fe',
    targetNutrients: ['Fe'],
    desc: 'Center of spectral mass / spectral wavelength centroid with safe interpolation',
    formula: 'Centroid=(iS[i])/S[i], t=clamp((C_S - C_MIN)/(C_MAX - C_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function sc(vec) {
        const num = vec.reduce((a, val, i) => a + i * val, 0);
        const den = vec.reduce((a, val) => a + val, 0) + 1e-10;
        return num / den;
      }
      const cS = sc(s);
      const cMin = sc(d.min);
      const cMax = sc(d.max);
      const denom = Math.abs(cMax - cMin) > 1e-10 ? (cMax - cMin) : 1e-10;
      const t = clamp((cS - cMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 19,
    name: 'Spectral Curvature',
    code: 'M19',
    targetNutrient: 'Mn',
    targetNutrients: ['Mn'],
    desc: 'Second derivative spectral curvature (B14 - 2B16 + B18) with safe interpolation',
    formula: 'Curv=B14 - 2B16 + B18, t=clamp((Curv_S - Curv_MIN)/(Curv_MAX - Curv_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function curv(vec) {
        return (vec[14] || 0) - 2 * (vec[16] || 0) + (vec[18] || 0);
      }
      const cS = curv(s);
      const cMin = curv(d.min);
      const cMax = curv(d.max);
      const denom = Math.abs(cMax - cMin) > 1e-10 ? (cMax - cMin) : 1e-10;
      const t = clamp((cS - cMin) / denom, 0, 1);
      return d.vals[0] + t * (d.vals[2] - d.vals[0]);
    }
  },
  {
    id: 20,
    name: 'Gain Corrected',
    code: 'M20',
    targetNutrient: 'Cu',
    targetNutrients: ['Cu'],
    desc: 'Geometric mean ratio gain factor ((B18/B10)  (B14/B9)) with safe interpolation',
    formula: 'Gain=((B18/B10)(B14/B9)), t=clamp((G_S - G_MIN)/(G_MAX - G_MIN), 0, 1), Pred=MIN+t(MAX-MIN)',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 22,
    name: 'Blended Regression',
    code: 'M22',
    targetNutrient: 'K',
    targetNutrients: ['K'],
    desc: 'Hybrid ensemble blending Pearson correlation regression with Euclidean IDW based on confidence',
    formula: 'Pred_IDW(p=1.0), Pred_Reg(Pearson-weighted), Conf=1/(1+min(d)), Blend=(1-Conf)Reg + ConfIDW',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function pearson(v1, v2) {
        const m1 = v1.reduce((a, b) => a + b, 0) / v1.length;
        const m2 = v2.reduce((a, b) => a + b, 0) / v2.length;
        const num = v1.reduce((a, val, i) => a + (val - m1) * (v2[i] - m2), 0);
        const d1 = Math.sqrt(v1.reduce((a, val) => a + Math.pow(val - m1, 2), 0));
        const d2 = Math.sqrt(v2.reduce((a, val) => a + Math.pow(val - m2, 2), 0));
        return num / (d1 * d2 + 1e-10);
      }
      const dm = Math.sqrt(d.min.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dd = Math.sqrt(d.mid.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      const dx = Math.sqrt(d.max.reduce((a, v, i) => a + Math.pow(s[i] - v, 2), 0));
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      const predInterp = (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
      
      const rMin = Math.max(0, pearson(s, d.min));
      const rMid = Math.max(0, pearson(s, d.mid));
      const rMax = Math.max(0, pearson(s, d.max));
      const totR = rMin + rMid + rMax + 1e-10;
      const predReg = (rMin * d.vals[0] + rMid * d.vals[1] + rMax * d.vals[2]) / totR;
      
      const minD = Math.min(dm, dd, dx);
      const conf = 1 / (1 + minD);
      return (1 - conf) * predReg + conf * predInterp;
    }
  },
  {
    id: 23,
    name: 'Fingerprint Transform',
    code: 'M23',
    targetNutrient: 'Mg',
    targetNutrients: ['Mg'],
    desc: 'Normalized spectral fingerprint (norm[0]norm[1])/(norm[2]+) with Manhattan IDW (p=1.0)',
    formula: 'Norm=S/max|S|, FP=(Norm[0]Norm[1])/(Norm[2]+), d=|FP_S - FP_C|, w=1/(d+), Pred=(wV)/w',
    builtin: true,
    active: false,
    fn: function(d, s) {
      function getFp(vec) {
        const mx = Math.max(...vec.map(Math.abs)) + 1e-10;
        const norm = vec.map(x => x / mx);
        return (norm[0] * norm[1]) / ((norm[2] || 0) + 1e-10);
      }
      const fpS = getFp(s);
      const fpMin = getFp(d.min);
      const fpMid = getFp(d.mid);
      const fpMax = getFp(d.max);
      
      const dm = Math.abs(fpS - fpMin);
      const dd = Math.abs(fpS - fpMid);
      const dx = Math.abs(fpS - fpMax);
      
      const eps = 1e-10;
      const wm = 1 / (dm + eps), wd = 1 / (dd + eps), wx = 1 / (dx + eps);
      return (wm * d.vals[0] + wd * d.vals[1] + wx * d.vals[2]) / (wm + wd + wx);
    }
  },
  {
    id: 24,
    name: 'Piecewise Interpolation',
    code: 'M24',
    targetNutrient: 'Zn',
    targetNutrients: ['Zn'],
    desc: 'Spectral mean position piecewise interpolation through MIN  MID  MAX nodes',
    formula: 'Pos=(mean(S)-mean(MIN))/(mean(MAX)-mean(MIN)), Piecewise linear through MID',
    builtin: true,
    active: false,
    fn: function(d, s) {
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
    }
  },
  {
    id: 25,
    name: 'Similarity Weighted Interpolation',
    code: 'M25',
    targetNutrient: 'N',
    targetNutrients: ['N', 'OC'],
    desc: 'Per-wavelength Cauchy similarity metric S_i = 1/(|S[i]-C[i]| + 1) summed across all bands',
    formula: 'T_k =  1/(|S[i]-C_k[i]| + 1), W_k = T_k /  T, Pred = (W_k  V_k)',
    builtin: true,
    active: false,
    fn: function(d, s) {
      const sm = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.min[i]) + 1), 0);
      const sd = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.mid[i]) + 1), 0);
      const sx = s.reduce((a, val, i) => a + 1 / (Math.abs(val - d.max[i]) + 1), 0);
      const total = sm + sd + sx || 1;
      return (sm * d.vals[0] + sd * d.vals[1] + sx * d.vals[2]) / total;
    }
  }
];

