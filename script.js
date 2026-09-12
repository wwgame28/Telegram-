(() => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Motion Primitives-inspired blur/reveal: lightweight local implementation.
  const reveals = document.querySelectorAll('.reveal');
  if (prefersReduced || !('IntersectionObserver' in window)) {
    reveals.forEach(el => el.classList.add('in'));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -35px' });
    reveals.forEach((el, i) => {
      el.style.transitionDelay = `${Math.min((i % 5) * 55, 220)}ms`;
      io.observe(el);
    });
  }

  // Magic UI-style spotlight effect for interactive cards.
  document.querySelectorAll('[data-spotlight]').forEach(card => {
    card.addEventListener('pointermove', e => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - r.left}px`);
      card.style.setProperty('--my', `${e.clientY - r.top}px`);
    });
  });

  // Subtle magnetic action buttons on pointer devices.
  if (window.matchMedia('(pointer:fine)').matches && !prefersReduced) {
    document.querySelectorAll('.magnetic').forEach(btn => {
      btn.addEventListener('pointermove', e => {
        const r = btn.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) * 0.12;
        const y = (e.clientY - r.top - r.height / 2) * 0.12;
        btn.style.transform = `translate(${x}px, ${y}px)`;
      });
      btn.addEventListener('pointerleave', () => btn.style.transform = '');
    });

    const glow = document.querySelector('.cursor-glow');
    window.addEventListener('pointermove', e => {
      glow.style.left = `${e.clientX}px`;
      glow.style.top = `${e.clientY}px`;
      glow.style.opacity = '1';
    });
  }

  // Origin UI-style segmented filter behavior.
  const tabs = document.querySelectorAll('.tab');
  const works = document.querySelectorAll('.work-card');
  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const f = tab.dataset.filter;
    works.forEach(card => card.classList.toggle('hidden', f !== 'all' && card.dataset.category !== f));
  }));

  // Portfolio lightbox.
  const dlg = document.getElementById('lightbox');
  const dlgImg = document.getElementById('lightboxImg');
  const dlgTitle = document.getElementById('lightboxTitle');
  const dlgIndex = document.getElementById('lightboxIndex');
  works.forEach((card, idx) => card.addEventListener('click', () => {
    dlgImg.className = 'lightbox-sprite ' + card.dataset.sprite;
    dlgImg.setAttribute('aria-label', card.dataset.title || 'Работа ORLICA TATT');
    dlgTitle.textContent = card.dataset.title || 'Работа';
    dlgIndex.textContent = `ORLICA / ${String(idx + 1).padStart(2, '0')}`;
    if (typeof dlg.showModal === 'function') dlg.showModal();
  }));
  document.querySelector('.lightbox-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });

  // Style chips.
  let chosenStyle = 'Графика';
  document.querySelectorAll('.chip').forEach(chip => chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    chosenStyle = chip.dataset.value;
  }));

  // Privacy-friendly Telegram handoff. No data is sent to a backend.
  const form = document.getElementById('tattooForm');
  const status = document.getElementById('formStatus');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const idea = document.getElementById('idea').value.trim();
    const placement = document.getElementById('placement').value;
    const size = document.getElementById('size').value;
    const text = `Привет, Света! Хочу обсудить татуировку.\n\nИдея: ${idea}\nМесто: ${placement}\nРазмер: ${size}\nСтиль: ${chosenStyle}\n\nПодскажите, пожалуйста, по стоимости и ближайшим свободным датам.`;
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = 'Текст заявки скопирован. Открываю Telegram — просто вставь сообщение в чат.';
    } catch {
      status.textContent = 'Открываю Telegram. Текст заявки показан ниже: ' + text;
    }
    setTimeout(() => window.open('https://t.me/Sveta_orel09', '_blank', 'noopener,noreferrer'), 260);
  });
})();
