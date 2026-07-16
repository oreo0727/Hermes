const fs = require('fs');
const path = process.argv[2];
const src = fs.readFileSync(path, 'utf8');
try {
  new Function(src);
  console.log('OK');
} catch (e) {
  console.error('SYNTAX_ERROR:', e.message);
  process.exit(1);
}
