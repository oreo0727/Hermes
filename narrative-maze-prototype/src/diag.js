(function(){
  const el = document.createElement('div');
  el.id = 'diag-marker'; el.textContent = 'Renderer probe';
  el.style.position = 'fixed'; el.style.left='12px'; el.style.top='12px';
  el.style.zIndex = 9999; el.style.background = '#ff00ff'; el.style.color = '#000';
  el.style.padding='4px 6px'; el.style.borderRadius='6px'; el.style.fontSize='12px';
  el.style.fontFamily='monospace'; el.style.pointerEvents='none'; document.body.appendChild(el);

  function showError(msg){
    const o = document.getElementById('_err_') || document.createElement('pre');
    o.id = '_err_'; o.style.position='fixed'; o.style.right='12px'; o.style.top='12px'; o.style.zIndex=99999;
    o.style.background='#000'; o.style.color='#fff'; o.style.padding='8px'; o.style.fontFamily='monospace';
    o.style.maxWidth='50vw'; o.style.maxHeight='80vh'; o.style.overflow='auto'; o.style.whiteSpace='pre-wrap';
    o.textContent = (new Date()).toISOString() + "\n" + msg; document.body.appendChild(o); console.error(msg);
  }

  window.addEventListener('error', function(e){ try{ showError('Error: ' + (e && (e.message || e.error || e.toString()) || String(e)) + '\n' + (e && e.filename ? e.filename + ':' + e.lineno + ':' + e.colno : '')) }catch(_){/*ignore*/} });
  window.addEventListener('unhandledrejection', function(e){ try{ showError('UnhandledRejection: ' + (e && e.reason ? (e.reason.stack || e.reason) : String(e))); }catch(_){/*ignore*/} });

  console.debug('Diag probe loaded');
})();
