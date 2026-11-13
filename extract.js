const fs = require('fs');

const data = fs.readFileSync('plugins.js', 'utf8');

// Use regex to find all object blocks in the array. 
// This is slightly tricky, so let's execute the file in a sandbox and override stringification.
// Actually, since plugins.js defines `const plugins = [...]`, we can evaluate it and then for each plugin, we want its original JS string for the `fn`.
// The easiest way is regex matching `\{[\s\S]*?id:\s*(\d+)[\s\S]*?fn:\s*function\s*\([^)]*\)\s*\{[\s\S]*?\}\s*\}`

const run = () => {
    // We can just run plugins.js using eval if we modify it slightly
    let modified = data.replace('const plugins = [', 'module.exports = [');
    // strip out runPlugin and getPluginsMeta at the end
    modified = modified.replace(/function runPlugin[\s\S]*$/, '');
    modified = modified.replace(/function getPluginsMeta[\s\S]*$/, '');
    
    fs.writeFileSync('temp_plugins.js', modified);
    const plugins = require('./temp_plugins.js');
    
    // However, require() loses the function source code (it's a function object). But we can call .toString() on it!
    plugins.forEach(p => {
        const id = p.code || ('M' + p.id);
        
        // Definition
        const def = {
            logic_id: id,
            logic_name: p.name,
            target: p.targetNutrients,
            type: "Mathematical",
            required_wavelengths: [], // Not explicitly in the old plugins, so empty means all/dynamic
            calibration_required: true, // Old logics required calibration
            required_calibration: { "type": "min_mid_max" },
            formula: p.formula || "",
            steps: [],
            unit: "kg/ha", // Default fallback
            version: "v1.0",
            status: "Active"
        };
        fs.writeFileSync(`logics/definitions/${id}.json`, JSON.stringify(def, null, 2));
        
        // Implementation
        const fnStr = p.fn.toString();
        const impl = `function execute(d, s) {\n  const fn = ${fnStr};\n  return fn(d, s);\n}\nmodule.exports = execute;`;
        fs.writeFileSync(`logics/implementations/${id}.js`, impl);
    });
    
    console.log("Extracted " + plugins.length + " plugins.");
}

run();
