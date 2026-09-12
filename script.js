(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];

  const reveals = $$('.reveal');
  if (reduced || !('IntersectionObserver' in window)) reveals.forEach(el => el.classList.add('in'));
  else {
    const io = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in');
      io.unobserve(entry.target);
    }), {threshold:.12, rootMargin:'0px 0px -45px'});
    reveals.forEach((el,i) => { el.style.transitionDelay = `${Math.min((i%4)*55,165)}ms`; io.observe(el); });
  }

  $$('[data-spotlight]').forEach(card => card.addEventListener('pointermove', e => {
    const r = card.getBoundingClientRect();
    card.style.setProperty('--mx', `${e.clientX-r.left}px`);
    card.style.setProperty('--my', `${e.clientY-r.top}px`);
  }));

  if (matchMedia('(pointer:fine)').matches && !reduced) {
    const cursor = $('.cursor');
    addEventListener('pointermove', e => { cursor.style.left=`${e.clientX}px`; cursor.style.top=`${e.clientY}px`; cursor.style.opacity='1'; });
    $$('a,button,.work').forEach(el => {
      el.addEventListener('pointerenter',()=>cursor.classList.add('big'));
      el.addEventListener('pointerleave',()=>cursor.classList.remove('big'));
    });
    $$('.magnetic').forEach(el => {
      el.addEventListener('pointermove', e => {
        const r=el.getBoundingClientRect();
        el.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.11}px,${(e.clientY-r.top-r.height/2)*.11}px)`;
      });
      el.addEventListener('pointerleave',()=>el.style.transform='');
    });
  }

  const parallax = $$('.parallax');
  if (!reduced && matchMedia('(pointer:fine)').matches) {
    let ticking=false;
    addEventListener('scroll',()=>{
      if(ticking) return; ticking=true;
      requestAnimationFrame(()=>{
        const y=scrollY;
        parallax.forEach(el=> el.style.translate=`0 ${y*Number(el.dataset.speed||0)}px`);
        ticking=false;
      });
    },{passive:true});
  }

  const filters=$$('.filter'), works=$$('.work');
  filters.forEach(btn=>btn.addEventListener('click',()=>{
    filters.forEach(b=>b.classList.remove('active')); btn.classList.add('active');
    const f=btn.dataset.filter;
    works.forEach(card=>card.classList.toggle('hidden',f!=='all'&&card.dataset.category!==f));
  }));

  const dlg=$('#lightbox'), dlgImg=$('#lightboxImg');
  works.forEach((card,i)=>card.addEventListener('click',()=>{
    dlgImg.className=`lightbox-image sprite ${card.dataset.sprite}`;
    $('#lightboxTitle').textContent=card.dataset.title||'Работа';
    $('#lightboxIndex').textContent=`ORLICA / ${String(i+1).padStart(2,'0')}`;
    dlg.showModal?.();
  }));
  $('.lightbox-close')?.addEventListener('click',()=>dlg.close());
  dlg?.addEventListener('click',e=>{if(e.target===dlg) dlg.close()});

  let chosen='Графика';
  $$('.chip').forEach(chip=>chip.addEventListener('click',()=>{
    $$('.chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); chosen=chip.dataset.value;
  }));
  $('#tattooForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const idea=$('#idea').value.trim(), placement=$('#placement').value, size=$('#size').value;
    const msg=`Привет, Света! Хочу обсудить тату 👋\n\nИдея: ${idea}\nМесто: ${placement}\nРазмер: ${size}\nПо вайбу: ${chosen}`;
    try{await navigator.clipboard.writeText(msg); $('#formStatus').textContent='Сообщение скопировано. Открываю Telegram ✦';}
    catch{ $('#formStatus').textContent='Открываю Telegram. Текст можно скопировать отсюда: '+msg; }
    setTimeout(()=>window.open('https://t.me/Sveta_orel09','_blank','noopener'),250);
  });
})();
