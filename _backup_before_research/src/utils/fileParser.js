import * as XLSX from 'xlsx';

export const WAVELENGTH_ORDER = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940, 320, 280, 200];
export const ALL_TARGETS = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B'];

export function parseDataFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const rawJson = XLSX.utils.sheet_to_json(worksheet, { defval: '' });

        if (!rawJson || rawJson.length === 0) {
          reject(new Error('The uploaded file contains no data rows.'));
          return;
        }

        const headers = Object.keys(rawJson[0]);

        // Clean samples & ensure unique Sample_ID
        const samples = rawJson.map((row, idx) => {
          let sId = row['Sample_ID'] || row['Sample ID'] || row['Sample'] || row['sample_id'] || row['sample'] || row['ID'] || row['id'];
          if (sId === undefined || sId === null || String(sId).trim() === '') {
            sId = `Sample_${String(idx + 1).padStart(3, '0')}`;
          } else {
            sId = String(sId).trim();
          }

          const cleanedRow = { ...row, Sample_ID: sId };

          // Standardize nm_ wavelength keys
          WAVELENGTH_ORDER.forEach(w => {
            const val = row[`nm_${w}`] ?? row[String(w)] ?? row[w] ?? row[`${w}nm`] ?? row[`nm${w}`] ?? 0;
            cleanedRow[`nm_${w}`] = isNaN(parseFloat(val)) ? 0 : parseFloat(val);
          });

          return cleanedRow;
        });

        resolve({
          fileName: file.name,
          sheetName,
          samples,
          columns: headers,
          sampleCount: samples.length,
          columnCount: headers.length
        });
      } catch (err) {
        reject(new Error('Excel/CSV parsing error: ' + err.message));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file from disk'));
    reader.readAsArrayBuffer(file);
  });
}
