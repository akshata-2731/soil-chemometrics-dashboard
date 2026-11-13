const plugins = [
  {
    id: 1,
    name: 'Standard Euclidean + IDW',
    code: 'M1',
    targetNutrient: 'OC',
    targetNutrients: ['OC'],
    desc: 'Euclidean distance across spectrum with Inverse Distance Weighting (IDW p=1.0)',
    formula: 'd_i = √(Σ(S - C_i)²), w_i = 1/(d_i + ε), Pred = Σ(w_i × V_i) / Σw_i',
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
    formula: 'T(x)=tanh(x/max|s|), d=Σ|T(S)-T(C)|, w=1/(d+ε)², Pred=Σ(w×V)/Σw',
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
    formula: 'Ratio=S[i]/S[j], d=|Ratio_S - Ratio_C|, w=1/(d+ε)², Pred=Σ(w×V)/Σw',
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
    formula: 'W=|MAX-MIN|/Σspread, Index=Σ(S×W), t=(Idx_S - Idx_MIN)/(Idx_MAX - Idx_MIN), Pred=MIN+t×(MAX-MIN)',
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
    formula: 'Vote=argmin(|S[i]-C_k[i]|), Pred = (Votes_min×V_min + Votes_mid×V_mid + Votes_max×V_max) / Total',
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
    formula: 'Pred = 0.4 × z_local(2-nearest) + 0.6 × z_idw(p=1.0)',
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
    formula: 'V=MID-MIN, S=Sample-MIN, α=clamp((S·V)/(V·V), 0, 1), Pred=MIN + α×(MAX - MIN)',
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
    formula: 'W=spread/Σspread, α=clamp(Σ(W×S×V)/Σ(W×V²), 0, 1), Piecewise MIN→MID→MAX',
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
    formula: 'Norm=S/mean(S), W=spread/Σspread, d=√(Σ(W×(Norm_S - Norm_C)²)), IDW p=1.0',
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
    formula: '50 synthetic steps on MIN→MAX path, find top 3 nearest synthetic spectra, IDW p=1.0',
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
    formula: 'CRI = (B18+B19+B20)/(B6+B7), t=clamp((CRI_S - CRI_MIN)/(CRI_MAX - CRI_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    formula: 'Energy = Σ(spectrum), t=clamp((E_S - E_MIN)/(E_MAX - E_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    desc: 'Directional spectral vector projection along MIN→MID calibration axis',
    formula: 'V=MID-MIN, S=Sample-MIN, α=clamp((S·V)/(V·V), 0, 1), Pred=MIN + α×(MAX - MIN)',
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
    desc: 'Spectral Angle Mapper (SAM) measuring angle θ between spectral vectors, IDW (p=1.5)',
    formula: 'cos(θ)=(A·B)/(||A||×||B||), θ=arccos(cos θ), w=1/(θ+ε)^1.5, Pred=Σ(w×V)/Σw',
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
    desc: 'First derivative (spectral gradient Δs) with Euclidean distance and IDW (p=1.0)',
    formula: 'G[i]=S[i+1]-S[i], d=√(Σ(G_S - G_C)²), w=1/(d+ε), Pred=Σ(w×V)/Σw',
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
    formula: 'DRI=(B2+B4+B7)/B13, t=clamp((DRI_S - DRI_MIN)/(DRI_MAX - DRI_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    formula: 'Score=(B0/B1 + B1/B2 + B2/B3)/3, d=|Score_S - Score_C|, w=1/(d+ε), Pred=Σ(w×V)/Σw',
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
    formula: 'Centroid=Σ(i×S[i])/ΣS[i], t=clamp((C_S - C_MIN)/(C_MAX - C_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    desc: 'Second derivative spectral curvature (B14 - 2×B16 + B18) with safe interpolation',
    formula: 'Curv=B14 - 2×B16 + B18, t=clamp((Curv_S - Curv_MIN)/(Curv_MAX - Curv_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    desc: 'Geometric mean ratio gain factor √((B18/B10) × (B14/B9)) with safe interpolation',
    formula: 'Gain=√((B18/B10)×(B14/B9)), t=clamp((G_S - G_MIN)/(G_MAX - G_MIN), 0, 1), Pred=MIN+t×(MAX-MIN)',
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
    formula: 'Pred_IDW(p=1.0), Pred_Reg(Pearson-weighted), Conf=1/(1+min(d)), Blend=(1-Conf)×Reg + Conf×IDW',
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
    desc: 'Normalized spectral fingerprint (norm[0]×norm[1])/(norm[2]+ε) with Manhattan IDW (p=1.0)',
    formula: 'Norm=S/max|S|, FP=(Norm[0]×Norm[1])/(Norm[2]+ε), d=|FP_S - FP_C|, w=1/(d+ε), Pred=Σ(w×V)/Σw',
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
    desc: 'Spectral mean position piecewise interpolation through MIN → MID → MAX nodes',
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
    formula: 'T_k = Σ 1/(|S[i]-C_k[i]| + 1), W_k = T_k / Σ T, Pred = Σ(W_k × V_k)',
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

// Mapping nutrient to its default recommended plugin index
const NUTRIENT_DEFAULT_LOGIC_MAP = {
  OC: 0,   // M1: Standard Euclidean + IDW
  N:  1,   // M2: Fingerprint Tanh + Manhattan
  P:  2,   // M3: KNN Ratio Fusion
  K:  3,   // M4: Spectral Nutrient Index
  Ca: 5,   // M6: Unified Adaptive
  Mg: 7,   // M8: Weighted Projection
  S:  8,   // M9: 10-Step Advanced
  Fe: 9,   // M10: Dense Ladder
  Mn: 10,  // M11: Carbon Response
  Cu: 11,  // M12: Spectral Energy
  Zn: 12,  // M13: Projection Vector
  B:  13   // M14: Spectral Angle
};

// ============================================================
// PER-NUTRIENT LOGIC STATE
// ============================================================
const NUTRIENT_ORDER = ['OC','N','P','K','Ca','Mg','S','Fe','Mn','Cu','Zn','B'];

function defaultNutrientLogicState() {
  const state = {};
  NUTRIENT_ORDER.forEach(n => {
    const defaultIdx = NUTRIENT_DEFAULT_LOGIC_MAP[n] !== undefined ? NUTRIENT_DEFAULT_LOGIC_MAP[n] : 0;
    state[n] = { enabled: true, pluginIdx: defaultIdx };
  });
  return state;
}

let nutrientLogicState = (function() {
  try {
    const saved = JSON.parse(localStorage.getItem('nutrientLogicState'));
    if (saved && typeof saved === 'object') {
      // Validate all nutrients exist and have valid pluginIdx
      NUTRIENT_ORDER.forEach(n => {
        if (!saved[n] || typeof saved[n].pluginIdx !== 'number' || saved[n].pluginIdx < 0 || saved[n].pluginIdx >= plugins.length) {
          saved[n] = { enabled: true, pluginIdx: NUTRIENT_DEFAULT_LOGIC_MAP[n] !== undefined ? NUTRIENT_DEFAULT_LOGIC_MAP[n] : 0 };
        }
      });
      return saved;
    }
  } catch(e) {}
  return defaultNutrientLogicState();
})();

function saveNutrientLogicState() {
  localStorage.setItem('nutrientLogicState', JSON.stringify(nutrientLogicState));
}

// ============================================================
// NUTRIENT × LOGIC MATRIX BUILDER (DYNAMIC)
// ============================================================
function buildNutrientLogicMatrix() {
  const container = document.getElementById('nutrient-logic-matrix');
  if (!container) return;

  // Ensure all nutrients exist in state
  NUTRIENT_ORDER.forEach(n => {
    if (!nutrientLogicState[n]) {
      nutrientLogicState[n] = { enabled: true, pluginIdx: NUTRIENT_DEFAULT_LOGIC_MAP[n] || 0 };
    }
  });

  const header = `
    <div class="nlm-header">
      <span></span>
      <span>Parameter</span>
      <span>Logic / Algorithm Selection</span>
      <span></span>
    </div>`;

  const rows = NUTRIENT_ORDER.map(n => {
    const meta = nutrientMeta[n] || { fullName: n, color: '#58a6ff', cls: 'oc' };
    const st = nutrientLogicState[n];
    const enabled = st.enabled;
    const currentPluginIdx = (st.pluginIdx >= 0 && st.pluginIdx < plugins.length) ? st.pluginIdx : (NUTRIENT_DEFAULT_LOGIC_MAP[n] || 0);
    const curPlugin = plugins[currentPluginIdx] || plugins[0];

    // Filter recommended matching logics
    const recPlugins = [];
    const otherPlugins = [];

    plugins.forEach((p, idx) => {
      const isRec = p.targetNutrient === n || (p.targetNutrients && p.targetNutrients.includes(n));
      if (isRec) {
        recPlugins.push({ plugin: p, idx });
      } else {
        otherPlugins.push({ plugin: p, idx });
      }
    });

    let recOptions = '';
    if (recPlugins.length > 0) {
      recOptions = `<optgroup label="⭐ Recommended Matching Logics for ${n}">` +
        recPlugins.map(item => {
          const sel = item.idx === currentPluginIdx ? 'selected' : '';
          return `<option value="${item.idx}" ${sel}>${item.plugin.code}: ${item.plugin.name} (Matched)</option>`;
        }).join('') +
        `</optgroup>`;
    }

    const allOptions = `<optgroup label="All 24 Available Logics">` +
      plugins.map((p, idx) => {
        const sel = idx === currentPluginIdx ? 'selected' : '';
        const tag = p.targetNutrient ? ` [Target: ${p.targetNutrient}]` : '';
        return `<option value="${idx}" ${sel}>${p.code}: ${p.name}${tag}</option>`;
      }).join('') +
      `</optgroup>`;

    return `
      <div class="nlm-row ${enabled ? '' : 'disabled'}" id="nlm-row-${n}">
        <input type="checkbox" class="nlm-check" ${enabled ? 'checked' : ''}
          onchange="toggleNutrient('${n}', this.checked)" title="Enable/Disable ${n}">
        <div class="nlm-name">
          <span style="color:${meta.color}">${n}</span>
          <span class="nlm-sub">${(meta.fullName||n).replace('Phosphorus (P₂O₅)','Phosphorus')}</span>
        </div>
        <div style="width:100%">
          <select class="nlm-select" id="nlm-sel-${n}" ${enabled ? '' : 'disabled'}
            onchange="setNutrientLogic('${n}', this.value)">
            ${recOptions}
            ${allOptions}
          </select>
          <div class="nlm-formula-badge" id="nlm-badge-${n}" style="font-size:10px; color:var(--muted); margin-top:2px; font-family:'JetBrains Mono', monospace; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            <span style="color:var(--accent2); font-weight:600;">[${curPlugin.code}]</span> ${curPlugin.desc}
          </div>
        </div>
        <div class="nlm-dot" style="background:${meta.color}" title="${n}"></div>
      </div>`;
  }).join('');

  const actions = `
    <div class="nlm-actions">
      <button class="nlm-action-btn" onclick="nlmResetRecommended()" style="border-color:var(--accent2); color:var(--accent2); font-weight:600;">⭐ Reset to Recommended Logics</button>
      <button class="nlm-action-btn" onclick="nlmSelectAll(true)">✓ Enable All</button>
      <button class="nlm-action-btn" onclick="nlmSelectAll(false)">✕ Disable All</button>
      <button class="nlm-action-btn" onclick="nlmSetAllLogic(0)">All → M1 Euclidean</button>
      <button class="nlm-action-btn" onclick="nlmSetAllLogic(1)">All → M2 Fingerprint Tanh</button>
      <button class="nlm-action-btn" onclick="nlmSetAllLogic(23)">All → M25 Similarity</button>
    </div>`;

  container.innerHTML = header + rows + actions;
}

function toggleNutrient(n, enabled) {
  if (!nutrientLogicState[n]) nutrientLogicState[n] = { enabled: true, pluginIdx: 0 };
  nutrientLogicState[n].enabled = enabled;
  saveNutrientLogicState();
  const row = document.getElementById('nlm-row-' + n);
  const sel = document.getElementById('nlm-sel-' + n);
  if (row) row.classList.toggle('disabled', !enabled);
  if (sel) sel.disabled = !enabled;
  
  // Dynamic live update if sample inputs exist
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    const results = predictAll(sample);
    renderResults(results);
    updateCharts();
  }
}

function setNutrientLogic(n, val) {
  const pluginIdx = parseInt(val, 10);
  if (!nutrientLogicState[n]) nutrientLogicState[n] = { enabled: true, pluginIdx: 0 };
  nutrientLogicState[n].pluginIdx = pluginIdx;
  saveNutrientLogicState();
  
  // Update badge description
  const p = plugins[pluginIdx] || plugins[0];
  const badge = document.getElementById('nlm-badge-' + n);
  if (badge && p) {
    badge.innerHTML = `<span style="color:var(--accent2); font-weight:600;">[${p.code}]</span> ${p.desc}`;
  }
  
  // Dynamic live update
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    const results = predictAll(sample);
    renderResults(results);
    updateCharts();
  }
}

function nlmResetRecommended() {
  NUTRIENT_ORDER.forEach(n => {
    const recIdx = NUTRIENT_DEFAULT_LOGIC_MAP[n] !== undefined ? NUTRIENT_DEFAULT_LOGIC_MAP[n] : 0;
    nutrientLogicState[n].pluginIdx = recIdx;
    nutrientLogicState[n].enabled = true;
    const cb = document.querySelector(`#nlm-row-${n} .nlm-check`);
    const sel = document.getElementById('nlm-sel-' + n);
    const row = document.getElementById('nlm-row-' + n);
    const badge = document.getElementById('nlm-badge-' + n);
    if (cb) cb.checked = true;
    if (sel) { sel.value = recIdx; sel.disabled = false; }
    if (row) row.classList.remove('disabled');
    const p = plugins[recIdx] || plugins[0];
    if (badge && p) {
      badge.innerHTML = `<span style="color:var(--accent2); font-weight:600;">[${p.code}]</span> ${p.desc}`;
    }
  });
  saveNutrientLogicState();
  
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    const results = predictAll(sample);
    renderResults(results);
    updateCharts();
  }
}

function nlmSelectAll(enabled) {
  NUTRIENT_ORDER.forEach(n => {
    if (!nutrientLogicState[n]) nutrientLogicState[n] = { enabled: true, pluginIdx: 0 };
    nutrientLogicState[n].enabled = enabled;
    const cb = document.querySelector(`#nlm-row-${n} .nlm-check`);
    const sel = document.getElementById('nlm-sel-' + n);
    const row = document.getElementById('nlm-row-' + n);
    if (cb) cb.checked = enabled;
    if (sel) sel.disabled = !enabled;
    if (row) row.classList.toggle('disabled', !enabled);
  });
  saveNutrientLogicState();
  
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    const results = predictAll(sample);
    renderResults(results);
    updateCharts();
  }
}

function nlmSetAllLogic(idx) {
  NUTRIENT_ORDER.forEach(n => {
    if (!nutrientLogicState[n]) nutrientLogicState[n] = { enabled: true, pluginIdx: 0 };
    nutrientLogicState[n].pluginIdx = idx;
    const sel = document.getElementById('nlm-sel-' + n);
    const badge = document.getElementById('nlm-badge-' + n);
    if (sel) sel.value = idx;
    const p = plugins[idx] || plugins[0];
    if (badge && p) {
      badge.innerHTML = `<span style="color:var(--accent2); font-weight:600;">[${p.code}]</span> ${p.desc}`;
    }
  });
  saveNutrientLogicState();
  
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    const results = predictAll(sample);
    renderResults(results);
    updateCharts();
  }
}

// ============================================================
// INIT
// ============================================================
window.onload = function() {
  buildNutrientLogicMatrix();
  initCharts();
  buildWavelengthInputs();
  if (typeof buildPluginList === 'function') buildPluginList();
  if (typeof buildCalEditor === 'function') buildCalEditor();
  if (typeof buildNutrientConfigList === 'function') buildNutrientConfigList();
  if (typeof buildUnitsEditor === 'function') buildUnitsEditor();
  if (typeof buildWlLabelsEditor === 'function') buildWlLabelsEditor();
};

// ============================================================
// TAB SWITCHING
// ============================================================
function switchTab(id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  if (event && event.currentTarget) event.currentTarget.classList.add('active');
  const panel = document.getElementById('panel-' + id);
  if (panel) panel.classList.add('active');
  if (id === 'calibration' && typeof buildCalEditor === 'function') buildCalEditor();
  if (id === 'logic' && typeof buildPluginList === 'function') buildPluginList();
  if (id === 'history' && typeof renderHistory === 'function') renderHistory();
  if (id === 'settings') {
    if (typeof buildUnitsEditor === 'function') buildUnitsEditor();
    if (typeof buildWlLabelsEditor === 'function') buildWlLabelsEditor();
  }
}

// ============================================================
// WAVELENGTH INPUTS
// ============================================================
function buildWavelengthInputs() {
  const container = document.getElementById('wavelength-inputs');
  if (!container) return;
  container.innerHTML = '';
  wavelengths.forEach((wl, idx) => {
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
      <div class="input-label">
        <span class="wavelength-badge">${wl.nm}nm</span>
        <span style="color:var(--text);">${wl.label} [${idx}]</span>
      </div>
      <input type="number" id="wl-${idx}" placeholder="0.00" step="0.01" oninput="onInputChanged()">
    `;
    container.appendChild(div);
  });
}

function onInputChanged() {
  const sample = getSampleValues();
  if (sample.some(v => v !== 0)) {
    updateCharts();
  }
}

function clearInputs() {
  for (let i = 0; i < 21; i++) {
    const el = document.getElementById('wl-' + i);
    if (el) el.value = '';
  }
  document.getElementById('nutrient-results').style.display = 'none';
  document.getElementById('results-table-card').style.display = 'none';
  document.getElementById('results-placeholder').style.display = 'block';
  updateCharts();
}

function loadSampleRow() {
  SAMPLE_ROW.forEach((v, i) => {
    const el = document.getElementById('wl-' + i);
    if (el) el.value = v;
  });
  runPrediction();
}

function pasteCSV() {
  document.getElementById('paste-modal').style.display = 'flex';
  document.getElementById('paste-input').focus();
}

function closePasteModal() {
  document.getElementById('paste-modal').style.display = 'none';
}

function applyPaste() {
  const raw = document.getElementById('paste-input').value;
  const vals = raw.split(/[,\t\s]+/).map(Number).filter(v => !isNaN(v));
  if (vals.length < 21) {
    alert(`Need 21 values, got ${vals.length}`);
    return;
  }
  vals.slice(0, 21).forEach((v, i) => {
    const el = document.getElementById('wl-' + i);
    if (el) el.value = v;
  });
  closePasteModal();
  runPrediction();
}

function getSampleValues() {
  const vals = [];
  for (let i = 0; i < 21; i++) {
    const el = document.getElementById('wl-' + i);
    vals.push(el ? parseFloat(el.value) || 0 : 0);
  }
  return vals;
}

// ============================================================
// PREDICTION ENGINE (DYNAMIC PER-NUTRIENT)
// ============================================================
function predictAll(sampleValues) {
  const results = {};

  for (const nutrient of NUTRIENT_ORDER) {
    const st = nutrientLogicState[nutrient];
    if (!st || !st.enabled) continue;

    const d = calData[nutrient];
    if (!d || !d.vals || !d.min || !d.mid || !d.max) continue;

    const pluginIdx = (st.pluginIdx >= 0 && st.pluginIdx < plugins.length) ? st.pluginIdx : (NUTRIENT_DEFAULT_LOGIC_MAP[nutrient] || 0);
    const plugin = plugins[pluginIdx] || plugins[0];

    try {
      const pred = plugin.fn(d, sampleValues);
      
      const Dm = d.min.reduce((a, v, i) => a + Math.abs(sampleValues[i] - (v || 0)), 0);
      const Dd = d.mid.reduce((a, v, i) => a + Math.abs(sampleValues[i] - (v || 0)), 0);
      const Dx = d.max.reduce((a, v, i) => a + Math.abs(sampleValues[i] - (v || 0)), 0);
      
      const Sm = 1 / (Dm + 1), Sd = 1 / (Dd + 1), Sx = 1 / (Dx + 1);
      const T = Sm + Sd + Sx || 1;

      results[nutrient] = {
        value: pred,
        pluginIdx,
        pluginCode: plugin.code,
        pluginName: plugin.name,
        pluginDesc: plugin.desc,
        pluginFormula: plugin.formula,
        Dm, Dd, Dx,
        Wm: Sm / T, Wd: Sd / T, Wx: Sx / T
      };
    } catch(e) {
      results[nutrient] = {
        value: 0,
        pluginIdx,
        pluginCode: plugin.code,
        pluginName: plugin.name,
        pluginDesc: plugin.desc,
        pluginFormula: plugin.formula,
        error: e.message,
        Dm: 0, Dd: 0, Dx: 0,
        Wm: 0, Wd: 0, Wx: 0
      };
    }
  }
  return results;
}

function runPrediction(isSilent = false) {
  const sample = getSampleValues();
  const allZero = sample.every(v => v === 0);
  if (allZero) {
    if (!isSilent) showAlert('warn', 'All inputs are zero. Please enter spectral values or load a sample row.');
    return;
  }

  const results = predictAll(sample);
  renderResults(results);
  updateCharts();

  if (settings.autoHistory && !isSilent) {
    const logicSummary = Object.keys(results).map(n => `${n}:${results[n].pluginCode || ('M' + ((results[n].pluginIdx||0)+1))}`).join(', ');
    predHistory.unshift({
      ts: new Date().toLocaleString(),
      sample: [...sample],
      results: {...results},
      plugin: logicSummary
    });
    if (predHistory.length > 50) predHistory.pop();
    saveState();
  }
}

function showAlert(type, msg) {
  const el = document.getElementById('results-placeholder');
  if (!el) return;
  el.style.display = 'block';
  el.className = 'alert alert-' + type;
  el.textContent = msg;
  const nr = document.getElementById('nutrient-results');
  if (nr) nr.style.display = 'none';
  const rtc = document.getElementById('results-table-card');
  if (rtc) rtc.style.display = 'none';
}

function renderResults(results) {
  const placeholder = document.getElementById('results-placeholder');
  if (placeholder) placeholder.style.display = 'none';

  const grid = document.getElementById('nutrient-results');
  if (grid) {
    grid.style.display = 'grid';
    grid.innerHTML = '';
  }

  const tbody = document.getElementById('results-tbody');
  if (tbody) tbody.innerHTML = '';
  const tableCard = document.getElementById('results-table-card');
  if (tableCard) tableCard.style.display = 'block';

  const dec = settings.decimals !== undefined ? settings.decimals : 4;

  for (const n of NUTRIENT_ORDER) {
    const res = results[n];
    if (!res) continue;

    const meta = nutrientMeta[n] || { fullName: n, unit: '', lo: 0, hi: 100, color: '#58a6ff', cls: 'oc' };
    const val = (typeof res.value === 'number' && !isNaN(res.value)) ? res.value.toFixed(dec) : '0.0000';
    
    let statusText = 'Optimal';
    let statusCls = 'badge-optimal';
    if (res.value < meta.lo) {
      statusText = 'Low';
      statusCls = 'badge-low';
    } else if (res.value > meta.hi) {
      statusText = 'High';
      statusCls = 'badge-high';
    }

    if (grid) {
      const card = document.createElement('div');
      card.className = 'nutrient-card';
      card.innerHTML = `
        <div class="flex-between">
          <div class="card-nutrient-name" style="color:${meta.color}">${n}</div>
          <span class="badge ${statusCls}">${statusText}</span>
        </div>
        <div class="card-nutrient-sub">${meta.fullName}</div>
        <div class="card-nutrient-val" style="color:var(--text); font-weight:700; font-size:22px; margin:8px 0;">
          ${val} <span style="font-size:12px; font-weight:400; color:var(--muted);">${meta.unit}</span>
        </div>
        
        <div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(195,230,203,0.3);">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:10px; color:var(--muted);">Logic:</span>
            <span class="badge" style="background:rgba(88,166,255,0.15); color:var(--accent2); font-weight:600; font-size:10px; padding:2px 6px;">
              [${res.pluginCode}] ${res.pluginName}
            </span>
          </div>
          <div style="font-size:9.5px; color:var(--muted); margin-top:3px; font-family:'JetBrains Mono', monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${res.pluginFormula}">
            ${res.pluginFormula}
          </div>
        </div>
      `;
      grid.appendChild(card);
    }

    if (tbody) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="color:${meta.color}">${n}</strong></td>
        <td>${meta.fullName}</td>
        <td class="num" style="font-weight:700; color:var(--text);">${val}</td>
        <td>${meta.unit}</td>
        <td>${meta.lo} - ${meta.hi}</td>
        <td><span class="badge ${statusCls}">${statusText}</span></td>
        <td><span class="badge" style="background:rgba(88,166,255,0.15); color:var(--accent2); font-size:11px; font-weight:600;">[${res.pluginCode}]</span> <span style="font-size:11px;">${res.pluginName}</span></td>
        <td class="num">${res.Dm !== undefined ? res.Dm.toFixed(2) : '-'}</td>
        <td class="num">${res.Dd !== undefined ? res.Dd.toFixed(2) : '-'}</td>
        <td class="num">${res.Dx !== undefined ? res.Dx.toFixed(2) : '-'}</td>
        <td class="num">${res.Wm !== undefined ? (res.Wm * 100).toFixed(1) + '%' : '-'}</td>
        <td class="num">${res.Wd !== undefined ? (res.Wd * 100).toFixed(1) + '%' : '-'}</td>
        <td class="num">${res.Wx !== undefined ? (res.Wx * 100).toFixed(1) + '%' : '-'}</td>
      `;
      tbody.appendChild(tr);
    }
  }
}

// ============================================================
// CHARTS (CHART.JS)
// ============================================================
let chartSpectral = null;
let chartCalibration = null;

function initCharts() {
  const ctxSpec = document.getElementById('chart-spectral');
  if (ctxSpec) {
    chartSpectral = new Chart(ctxSpec.getContext('2d'), {
      type: 'line',
      data: {
        labels: wavelengths.map(w => `${w.nm}nm`),
        datasets: [{
          label: 'Current Sample',
          data: wavelengths.map(() => 0),
          borderColor: '#238636',
          backgroundColor: 'rgba(35,134,54,0.15)',
          tension: 0.3,
          borderWidth: 2.5,
          fill: true,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#1f2328', font: { family: 'JetBrains Mono', size: 11 } } } },
        scales: {
          x: { ticks: { color: '#57606a', font: { size: 9 } }, grid: { color: 'rgba(195,230,203,0.3)' } },
          y: { ticks: { color: '#57606a', font: { size: 9 } }, grid: { color: 'rgba(195,230,203,0.3)' } }
        }
      }
    });
  }

  const ctxCal = document.getElementById('chart-calibration');
  if (ctxCal) {
    chartCalibration = new Chart(ctxCal.getContext('2d'), {
      type: 'line',
      data: {
        labels: wavelengths.map(w => `${w.nm}nm`),
        datasets: []
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#1f2328', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: {
          x: { ticks: { color: '#57606a', font: { size: 9 } }, grid: { color: 'rgba(195,230,203,0.3)' } },
          y: { ticks: { color: '#57606a', font: { size: 9 } }, grid: { color: 'rgba(195,230,203,0.3)' } }
        }
      }
    });
  }
}

function updateCharts() {
  const sample = getSampleValues();
  if (chartSpectral) {
    chartSpectral.data.labels = wavelengths.map(w => `${w.nm}nm`);
    chartSpectral.data.datasets[0].data = sample;
    chartSpectral.update();
  }

  const targetEl = document.getElementById('targetNutrient');
  const targetNut = targetEl ? targetEl.value : 'All';
  const calCanvas = document.getElementById('chart-calibration');
  const calPlaceholder = document.getElementById('chart-calibration-placeholder');

  if (targetNut === 'All' || !calData[targetNut]) {
    if (calCanvas) calCanvas.style.display = 'none';
    if (calPlaceholder) calPlaceholder.style.display = 'block';
    return;
  }

  if (calCanvas) calCanvas.style.display = 'block';
  if (calPlaceholder) calPlaceholder.style.display = 'none';

  const d = calData[targetNut];
  const meta = nutrientMeta[targetNut] || { color: '#58a6ff' };

  if (chartCalibration && d) {
    chartCalibration.data.labels = wavelengths.map(w => `${w.nm}nm`);
    chartCalibration.data.datasets = [
      {
        label: `Sample Spectrum`,
        data: sample,
        borderColor: '#238636',
        borderWidth: 2.5,
        tension: 0.3,
        pointRadius: 3
      },
      {
        label: `MIN Reference (${d.vals[0]})`,
        data: d.min,
        borderColor: '#58a6ff',
        borderDash: [4, 4],
        borderWidth: 1.5,
        tension: 0.3,
        pointRadius: 2
      },
      {
        label: `MID Reference (${d.vals[1]})`,
        data: d.mid,
        borderColor: '#f0883e',
        borderDash: [4, 4],
        borderWidth: 1.5,
        tension: 0.3,
        pointRadius: 2
      },
      {
        label: `MAX Reference (${d.vals[2]})`,
        data: d.max,
        borderColor: '#ff7b72',
        borderDash: [4, 4],
        borderWidth: 1.5,
        tension: 0.3,
        pointRadius: 2
      }
    ];
    chartCalibration.update();
  }
}

// ============================================================
// BATCH PROCESSING
// ============================================================
function handleDrag(e, enter) {
  e.preventDefault();
  const dz = document.getElementById('dropZone');
  if (dz) dz.style.borderColor = enter ? 'var(--accent2)' : 'var(--border)';
}

function handleDrop(e) {
  e.preventDefault();
  handleDrag(e, false);
  const file = e.dataTransfer.files[0];
  if (file) processBatchFile(file);
}

function loadBatchFile(e) {
  const file = e.target.files[0];
  if (file) processBatchFile(file);
}

function processBatchFile(file) {
  const reader = new FileReader();
  reader.onload = function(evt) {
    parseBatchCSV(evt.target.result);
  };
  reader.readAsText(file);
}

function runBatch() {
  const text = document.getElementById('batchPaste').value.trim();
  if (!text) { alert('Please enter or upload CSV rows.'); return; }
  parseBatchCSV(text);
}

function clearBatch() {
  document.getElementById('batchPaste').value = '';
  document.getElementById('batch-results').style.display = 'none';
  batchResults = [];
}

function loadSampleBatch() {
  const rows = [
    [1159.21,208.78,998.73,281.32,468.92,923.83,386.57,469.43,338.56,94.0,41.0,15.0,572.86,183.57,68.98,46.0,110.09,356.73,86.629,3.611,2.644],
    [1861.48,426.04,1551.11,486.63,696.82,1124.74,524.96,588.01,391.81,107,44,19,660.18,198.08,73,49.75,119.99,368.23,598.59,9.22,7.48],
    [1020.32,211.94,956.79,288,493.17,919.26,398.38,479.16,345.54,95,40.15,15,580.26,186.94,70.03,46.19,110,363.75,65.36,3.71,2.57]
  ];
  document.getElementById('batchPaste').value = rows.map(r => r.join(', ')).join('\n');
  runBatch();
}

function parseBatchCSV(csvText) {
  const lines = csvText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const rows = [];
  for (const line of lines) {
    const vals = line.split(/[,\t\s]+/).map(Number).filter(v => !isNaN(v));
    if (vals.length >= 21) {
      rows.push(vals.slice(0, 21));
    }
  }
  if (rows.length === 0) {
    alert('Could not find any valid rows with 21 numeric values.');
    return;
  }
  processBatchRows(rows);
}

function processBatchRows(rows) {
  batchResults = [];
  const thead = document.getElementById('batch-thead');
  const tbody = document.getElementById('batch-tbody');

  let headHTML = '<tr><th>#</th>';
  NUTRIENT_ORDER.forEach(n => {
    if (nutrientLogicState[n] && nutrientLogicState[n].enabled) {
      const st = nutrientLogicState[n];
      const p = plugins[st.pluginIdx] || plugins[0];
      headHTML += `<th>${n} <span style="font-size:9px;color:var(--muted)">[${p.code}]</span></th>`;
    }
  });
  headHTML += '</tr>';
  thead.innerHTML = headHTML;
  tbody.innerHTML = '';

  const dec = settings.decimals !== undefined ? settings.decimals : 4;

  rows.forEach((sample, rowIdx) => {
    const res = predictAll(sample);
    batchResults.push({ rowIdx: rowIdx + 1, sample, res });

    const tr = document.createElement('tr');
    let rowHTML = `<td><strong>${rowIdx + 1}</strong></td>`;
    NUTRIENT_ORDER.forEach(n => {
      if (nutrientLogicState[n] && nutrientLogicState[n].enabled) {
        const r = res[n];
        const val = r ? (typeof r.value === 'number' ? r.value.toFixed(dec) : '0.0000') : '-';
        rowHTML += `<td class="num">${val}</td>`;
      }
    });
    tr.innerHTML = rowHTML;
    tbody.appendChild(tr);
  });

  document.getElementById('batch-results').style.display = 'block';
}

function exportBatchCSV() {
  if (batchResults.length === 0) return;
  const enabledNutrients = NUTRIENT_ORDER.filter(n => nutrientLogicState[n] && nutrientLogicState[n].enabled);
  let csv = 'Sample_Index,' + enabledNutrients.map(n => `${n}_(${plugins[nutrientLogicState[n].pluginIdx]?.code||'M1'})`).join(',') + '\n';

  batchResults.forEach(item => {
    const vals = enabledNutrients.map(n => item.res[n] ? item.res[n].value.toFixed(4) : '');
    csv += `${item.rowIdx},${vals.join(',')}\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `soil_prediction_batch_${Date.now()}.csv`;
  a.click();
}

</script>
</body>
</html