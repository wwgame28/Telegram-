(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = matchMedia('(pointer: coarse)').matches;
  const root = document.documentElement;
  const $ = (s, ctx = document) => ctx.querySelector(s);
  const $$ = (s, ctx = document) => [...ctx.querySelectorAll(s)];

  root.dataset.designStack = 'orlica-pro';
  if (!reduced) root.classList.add('motion-enhanced');

  const hero = $('.hero-visual');
  const gallery = $('.gallery');
  const about = $('.about-collage');

  hero?.setAttribute('data-motion', 'iso-focus');
  gallery?.setAttribute('data-motion', 'iso-cascade');
  about?.setAttribute('data-motion', 'dynamic-editorial');

  // Iso Focus: layered perspective that keeps the original composition and imagery intact.
  if (hero && !reduced && !coarse) {
    const a = $('.hero-photo-a', hero);
    const b = $('.hero-photo-b', hero);
    let raf = 0;

    const apply = (clientX, clientY) => {
      const r = hero.getBoundingClientRect();
      const nx = Math.max(-1, Math.min(1, ((clientX - r.left) / r.width - .5) * 2));
      const ny = Math.max(-1, Math.min(1, ((clientY - r.top) / r.height - .5) * 2));

      if (a) {
        a.style.setProperty('--ds-a-x', `${nx * 11}px`);
        a.style.setProperty('--ds-a-y', `${ny * 7}px`);
        a.style.setProperty('--ds-a-z', '26px');
        a.style.setProperty('--ds-a-rx', `${-ny * 3.2}deg`);
        a.style.setProperty('--ds-a-ry', `${nx * 4.2}deg`);
      }
      if (b) {
        b.style.setProperty('--ds-b-x', `${-nx * 8}px`);
        b.style.setProperty('--ds-b-y', `${-ny * 5}px`);
        b.style.setProperty('--ds-b-z', '45px');
        b.style.setProperty('--ds-b-rx', `${ny * 2.4}deg`);
        b.style.setProperty('--ds-b-ry', `${-nx * 3.4}deg`);
      }
    };

    hero.addEventListener('pointermove', (e) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => apply(e.clientX, e.clientY));
    }, {passive: true});

    hero.addEventListener('pointerleave', () => {
      [a, b].forEach((el) => {
        if (!el) return;
        ['--ds-a-x','--ds-a-y','--ds-a-z','--ds-a-rx','--ds-a-ry','--ds-b-x','--ds-b-y','--ds-b-z','--ds-b-rx','--ds-b-ry']
          .forEach((name) => el.style.removeProperty(name));
      });
    });
  }

  // Iso Cascade: editorial cards enter as a controlled modular sequence.
  const cards = $$('.work', gallery || document);
  cards.forEach((card, i) => card.style.setProperty('--ds-delay', `${Math.min(i * 58, 320)}ms`));

  if (!reduced && 'IntersectionObserver' in window && gallery) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('motion-in');
        io.unobserve(entry.target);
      });
    }, {threshold: .08, rootMargin: '0px 0px -30px'});
    cards.forEach((card) => io.observe(card));
  } else {
    cards.forEach((card) => card.classList.add('motion-in'));
  }

  // Dynamic composition: one cheap scroll variable, shared by CSS. No heavy timeline library.
  if (!reduced) {
    let ticking = false;
    const update = () => {
      const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      root.style.setProperty('--ds-scroll', (scrollY / max).toFixed(4));
      ticking = false;
    };
    addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, {passive: true});
    update();
  }
})();
