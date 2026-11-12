const fs = require('fs');
const path = require('path');

const dir = 'C:/Users/Prasa/fc-posters/assets/';
const files = ['hyd-skyline.jpg', 'hyd-metro.jpg', 'hyd-tech.jpg'];
let output = 'const HYD_IMAGES = {\n';

files.forEach(file => {
  const filePath = path.join(dir, file);
  if (fs.existsSync(filePath)) {
    const key = file.replace('.jpg', '').replace(/-/g, '_');
    const b64 = fs.readFileSync(filePath).toString('base64');
    output += `  "${key}": "data:image/jpeg;base64,${b64}",\n`;
    console.log(`Encoded ${file} (${b64.length} chars)`);
  }
});

output += '};\n';
fs.writeFileSync(path.join(dir, 'images.js'), output);
console.log('Successfully written images.js');
