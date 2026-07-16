const fs=require('fs');
const path=process.argv[2];
const pos=parseInt(process.argv[3],10)||0;
const s=fs.readFileSync(path,'utf8');
const start=Math.max(0,pos-120);
const end=Math.min(s.length,pos+120);
console.log('Context around',pos,':\n');
console.log(s.slice(start,end));
