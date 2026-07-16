const fs=require('fs');
const src=fs.readFileSync(process.argv[2],'utf8');
const stack=[];
const pairs={')':'(',']':'[','}':'{'};
for(let i=0;i<src.length;i++){
  const ch=src[i];
  if(ch==='"' || ch==="'" || ch==='`'){
    const q=ch; i++; while(i<src.length){ if(src[i]===q && src[i-1]!=="\\"){ break; } i++; }
    continue;
  }
  if(ch==='('||ch==='['||ch==='{') stack.push({ch,pos:i});
  else if(ch===')'||ch===']'||ch==='}'){
    if(!stack.length || stack[stack.length-1].ch!==pairs[ch]){
      console.log('Mismatch at', i, 'found', ch, 'expected', stack.length?stack[stack.length-1].ch:'none');
      process.exit(1);
    }
    stack.pop();
  }
}
if(stack.length){ console.log('Unclosed bracket', stack[stack.length-1]); process.exit(1);} else { console.log('Brackets OK'); }
