const fs = require('fs');
const vm = require('vm');
const path = process.argv[2];
const src = fs.readFileSync(path, 'utf8');
try {
  new vm.Script(src, {filename: path});
  console.log('OK');
} catch (e) {
  console.error('SYNTAX_ERROR:', e.message);
  if (e.stack) console.error(e.stack.split('\n').slice(0,4).join('\n'));
  process.exit(1);
}
