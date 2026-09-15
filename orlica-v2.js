(() => {
  'use strict';

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(pointer:fine)').matches;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

  document.documentElement.classList.add('js');

  /* Intro gate: intentionally click-to-enter, per the ORLICA concept. */
  const gate = $('#introGate');
  const enter = $('#enterSite');
  const closeGate = () => {
    if (!gate || gate.classList.contains('exit')) return;
    gate.classList.add('exit');
    gate.setAttribute('aria-hidden', 'true');
    document.body.classList.add('entered');
    setTimeout(() => gate.remove(), reduced ? 30 : 1100);
  };
  enter?.addEventListener('click', closeGate);
  enter?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      closeGate();
    }
  });

  /* Scroll reveal, 21st/SmoothUI-style motion primitives implemented locally. */
  const revealEls = $$('.reveal-up, .reveal-scale');
  if (reduced || !('IntersectionObserver' in window)) {
    revealEls.forEach(el => el.classList.add('in'));
  } else {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in');
        revealObserver.unobserve(entry.target);
      });
    }, { threshold: .12, rootMargin: '0px 0px -8% 0px' });
    revealEls.forEach((el, i) => {
      el.style.transitionDelay = `${Math.min((i % 4) * 55, 165)}ms`;
      revealObserver.observe(el);
    });
  }

  /* Animos-inspired Iso Cascade for the modular gallery. */
  const isoCards = $$('.iso-card');
  isoCards.forEach((card, i) => card.style.setProperty('--delay', `${Math.min(i * 55, 330)}ms`));
  if (reduced || !('IntersectionObserver' in window)) {
    isoCards.forEach(card => card.classList.add('motion-in'));
  } else {
    const cascadeObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('motion-in');
        cascadeObserver.unobserve(entry.target);
      });
    }, { threshold: .08, rootMargin: '0px 0px -40px' });
    isoCards.forEach(card => cascadeObserver.observe(card));
  }

  /* Header, scroll progress, split paragraph reveal and MotionSites-like scroll choreography. */
  const header = $('#siteHeader');
  const progress = $('.scroll-progress span');
  const statement = $('.split-reveal');
  const heroMedia = $('#heroMedia');
  let lastY = 0;
  let ticking = false;

  const onScrollFrame = () => {
    const y = scrollY;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const ratio = y / max;
    progress && (progress.style.transform = `scaleX(${ratio})`);

    if (header) {
      header.classList.toggle('scrolled', y > 18);
      header.classList.toggle('hidden', y > lastY && y > 420);
    }

    if (statement) {
      const r = statement.getBoundingClientRect();
      const p = clamp((innerHeight - r.top) / (innerHeight * .85), 0, 1);
      statement.style.setProperty('--reveal', `${(p * 100).toFixed(1)}%`);
    }

    if (heroMedia && !reduced) {
      const p = clamp(y / Math.max(innerHeight, 1), 0, 1.3);
      heroMedia.style.translate = `0 ${p * 28}px`;
      heroMedia.style.rotate = `${p * .45}deg`;
    }

    lastY = y;
    ticking = false;
  };

  addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(onScrollFrame);
  }, { passive: true });
  onScrollFrame();

  /* SmoothUI-style magnetic buttons. */
  if (finePointer && !reduced) {
    $$('.magnetic').forEach((el) => {
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) * .12;
        const y = (e.clientY - r.top - r.height / 2) * .12;
        el.style.transform = `translate3d(${x}px,${y}px,0)`;
      });
      el.addEventListener('pointerleave', () => { el.style.transform = ''; });
    });
  }

  /* Custom cursor follow, disabled on touch. */
  if (finePointer && !reduced) {
    const cursor = $('.cursor-follower');
    const cursorText = cursor?.querySelector('i');
    let cx = innerWidth / 2, cy = innerHeight / 2, tx = cx, ty = cy;

    addEventListener('pointermove', (e) => {
      tx = e.clientX; ty = e.clientY;
      cursor?.classList.add('active');
    }, { passive: true });

    const animateCursor = () => {
      cx += (tx - cx) * .2;
      cy += (ty - cy) * .2;
      if (cursor) cursor.style.left = `${cx}px`, cursor.style.top = `${cy}px`;
      requestAnimationFrame(animateCursor);
    };
    animateCursor();

    $$('[data-cursor], a, button').forEach((el) => {
      el.addEventListener('pointerenter', () => {
        cursor?.classList.add('big');
        if (cursorText) cursorText.textContent = el.dataset.cursor || 'OPEN';
      });
      el.addEventListener('pointerleave', () => {
        cursor?.classList.remove('big');
        if (cursorText) cursorText.textContent = '';
      });
    });
  }

  /* Animos-inspired Iso Focus on Svetа portrait, without changing the actual photo. */
  if (heroMedia && finePointer && !reduced) {
    const photo = $('.hero-photo-shell', heroMedia);
    const noteA = $('.note-a', heroMedia);
    const noteB = $('.note-b', heroMedia);

    heroMedia.addEventListener('pointermove', (e) => {
      const r = heroMedia.getBoundingClientRect();
      const nx = clamp(((e.clientX - r.left) / r.width - .5) * 2, -1, 1);
      const ny = clamp(((e.clientY - r.top) / r.height - .5) * 2, -1, 1);
      if (photo) photo.style.transform = `translate3d(${nx * 10}px,${ny * 7}px,22px) rotateX(${-ny * 2.4}deg) rotateY(${nx * 3.8}deg) rotateZ(-1.3deg)`;
      if (noteA) noteA.style.transform = `translate3d(${nx * 16}px,${ny * 10}px,70px)`;
      if (noteB) noteB.style.transform = `translate3d(${-nx * 10}px,${-ny * 8}px,55px) rotate(-7deg)`;
    });
    heroMedia.addEventListener('pointerleave', () => {
      if (photo) photo.style.transform = '';
      if (noteA) noteA.style.transform = '';
      if (noteB) noteB.style.transform = '';
    });
  }

  /* SmoothUI spotlight cards. */
  $$('[data-spotlight]').forEach((card) => {
    card.addEventListener('pointermove', (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - r.left}px`);
      card.style.setProperty('--my', `${e.clientY - r.top}px`);
    });
  });

  /* Gallery filters + accessible lightbox. */
  const filters = $$('.filter');
  const works = $$('.work-card');
  const lightbox = $('#lightbox');
  const lightboxImg = $('#lightboxImg');
  const lightboxTitle = $('#lightboxTitle');
  const lightboxIndex = $('#lightboxIndex');

  filters.forEach((btn) => btn.addEventListener('click', () => {
    filters.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    works.forEach((card) => {
      const hidden = filter !== 'all' && card.dataset.category !== filter;
      card.classList.toggle('hidden', hidden);
    });
  }));

  works.forEach((card, i) => card.addEventListener('click', () => {
    if (!lightbox || !lightboxImg) return;
    lightboxImg.className = `lightbox-image sprite ${card.dataset.sprite || ''}`;
    lightboxTitle && (lightboxTitle.textContent = card.dataset.title || 'Работа');
    lightboxIndex && (lightboxIndex.textContent = `ORLICA / ${String(i + 1).padStart(2, '0')}`);
    if (typeof lightbox.showModal === 'function') lightbox.showModal();
  }));

  $('.lightbox-close')?.addEventListener('click', () => lightbox?.close());
  lightbox?.addEventListener('click', (e) => {
    if (e.target === lightbox) lightbox.close();
  });

  /* FAQ: keep one item open at a time, because accordion chaos is a choice. */
  const faqItems = $$('.faq-item');
  faqItems.forEach((item) => item.addEventListener('toggle', () => {
    if (!item.open) return;
    faqItems.forEach((other) => { if (other !== item) other.open = false; });
  }));

  /* Booking chips + Telegram message builder. */
  let chosen = 'Графика';
  $$('.chip').forEach((chip) => chip.addEventListener('click', () => {
    $$('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    chosen = chip.dataset.value || 'Графика';
  }));

  $('#tattooForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const idea = $('#idea')?.value.trim() || '';
    const placement = $('#placement')?.value || '';
    const size = $('#size')?.value || '';
    const status = $('#formStatus');

    if (!idea) {
      status && (status.textContent = 'Напиши хотя бы пару слов про идею. Телепатия пока в бете.');
      $('#idea')?.focus();
      return;
    }

    const message = `Привет, Света! Хочу обсудить тату ✦\n\nИдея: ${idea}\nМесто: ${placement}\nРазмер: ${size}\nПо вайбу: ${chosen}`;
    try {
      await navigator.clipboard.writeText(message);
      status && (status.textContent = 'Сообщение скопировано. Открываю Telegram…');
    } catch {
      status && (status.textContent = 'Открываю Telegram. Текст сохранён здесь: ' + message);
    }

    const url = `https://t.me/Sveta_orel09?text=${encodeURIComponent(message)}`;
    setTimeout(() => window.open(url, '_blank', 'noopener,noreferrer'), 180);
  });

  /* Pause decorative marquee off-screen to avoid wasting mobile battery. */
  const ticker = $('.ticker-track');
  if (ticker && 'IntersectionObserver' in window) {
    const tickerObserver = new IntersectionObserver(([entry]) => {
      ticker.style.animationPlayState = entry.isIntersecting ? 'running' : 'paused';
    });
    tickerObserver.observe(ticker);
  }
})();