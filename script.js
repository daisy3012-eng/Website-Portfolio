const header = document.querySelector('.site-header');
const navToggle = header.querySelector('.nav-toggle');
const mainNavigation = header.querySelector('nav');
const mobileNavigation = window.matchMedia('(max-width: 800px)');
const menuBackground = [...document.querySelectorAll('body > main, body > footer')];
function setNavigationOpen(open, restoreFocus = false) {
  header.classList.toggle('menu-open', open);
  const mobileOpen = open && mobileNavigation.matches;
  document.documentElement.classList.toggle('mobile-menu-open', mobileOpen);
  for (const element of menuBackground) element.inert = mobileOpen;
  navToggle.setAttribute('aria-expanded', String(open));
  navToggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
  if (restoreFocus) navToggle.focus({ preventScroll: true });
}
header.classList.add('has-mobile-menu');
navToggle.addEventListener('click', () => {
  setNavigationOpen(navToggle.getAttribute('aria-expanded') !== 'true');
});
header.addEventListener('click', event => {
  if (mobileNavigation.matches && event.target.closest('a')) setNavigationOpen(false, true);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Tab' && mobileNavigation.matches && header.classList.contains('menu-open')) {
    const firstLink = header.querySelector('.site-logo') || navToggle;
    const lastLink = mainNavigation.querySelector('a:last-child');
    if (event.shiftKey && document.activeElement === firstLink) {
      event.preventDefault();
      lastLink.focus();
    } else if (!event.shiftKey && document.activeElement === lastLink) {
      event.preventDefault();
      firstLink.focus();
    }
  }
  if (event.key === 'Escape' && header.classList.contains('menu-open')) {
    setNavigationOpen(false, true);
  }
});
document.addEventListener('click', event => {
  if (!header.contains(event.target)) setNavigationOpen(false);
});
header.addEventListener('focusout', event => {
  if (!header.contains(event.relatedTarget)) setNavigationOpen(false);
});
mobileNavigation.addEventListener('change', () => {
  const focused = document.activeElement;
  setNavigationOpen(false);
  if (mobileNavigation.matches && mainNavigation.contains(focused)) navToggle.focus();
  else if (!mobileNavigation.matches && focused === navToggle) mainNavigation.querySelector('a').focus();
});
window.addEventListener('pageshow', () => setNavigationOpen(false));
let headerHeight = 0;
function measureHeader() {
  const height = header.getBoundingClientRect().height;
  if (height === headerHeight) return;
  headerHeight = height;
  document.documentElement.style.setProperty('--header-height', `${height}px`);
  window.ScrollTrigger?.refresh();
}
measureHeader();
new ResizeObserver(measureHeader).observe(header);
const sections = [...document.querySelectorAll('[data-theme]')];
let lastHeaderSection;
function updateHeader() {
  header.classList.toggle('scrolled', window.scrollY > 80);
  const sampleY = header.getBoundingClientRect().bottom + 1;
  const current = [...sections].reverse().find(section => {
    const rect = section.getBoundingClientRect();
    return rect.top <= sampleY && rect.bottom > sampleY;
  });
  if (lastHeaderSection === current && header.dataset.theme) return;
  lastHeaderSection = current;
  header.dataset.theme = current?.dataset.theme || 'light';
  // Match the section immediately below the reserved navigation row. Opaque
  // matching paint prevents scrolling text from crossing the navigation links.
  let background = current ? getComputedStyle(current).backgroundColor : '';
  if (!background || background === 'rgba(0, 0, 0, 0)' || background === 'transparent') {
    background = getComputedStyle(document.body).backgroundColor;
  }
  header.style.setProperty('--navigation-background', background);
  header.dataset.section = current?.id || '';
  document.documentElement.classList.toggle('contact-active', current?.id === 'contact');
  for (const link of header.querySelectorAll('a')) {
    if (current && link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}
// Apply theme changes in the scroll frame, without an extra animation-frame delay.
window.addEventListener('scroll', updateHeader, { passive: true });
window.addEventListener('resize', updateHeader);
window.addEventListener('pageshow', updateHeader);
document.fonts?.ready.then(updateHeader);
updateHeader();
// Animate disclosure height so neighboring skills move gently too.
const skills = [...document.querySelectorAll('.skill-list details')];
const hoverSkills = window.matchMedia('(hover: hover) and (pointer: fine)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const skillAnimations = new Map();
let hoverTimer;
let hoverTarget;
function setSkill(skill, expanded) {
  if ((skill.dataset.expanded === 'true') === expanded) return;
  const startHeight = skill.getBoundingClientRect().height;
  skillAnimations.get(skill)?.cancel();
  skill.dataset.expanded = String(expanded);
  skill.open = true;
  const style = getComputedStyle(skill);
  const verticalPadding = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
  const endHeight = expanded ? skill.getBoundingClientRect().height
    : skill.querySelector('summary').getBoundingClientRect().height + verticalPadding;
  if (reducedMotion.matches) {
    skill.open = expanded;
    skillAnimations.delete(skill);
    return;
  }
  const animation = skill.animate([
    { height: `${startHeight}px`, overflow: 'hidden' },
    { height: `${endHeight}px`, overflow: 'hidden' }
  ], { duration: 600, easing: 'cubic-bezier(.25, .1, .25, 1)' });
  skillAnimations.set(skill, animation);
  animation.onfinish = () => {
    skill.open = expanded;
    skillAnimations.delete(skill);
  };
}
function openSkill(skill) {
  skills.forEach(other => setSkill(other, other === skill));
}
for (const skill of skills) {
  // Native exclusivity remains the no-JS fallback. Animated panels must stay
  // open briefly while closing so their contents can slide out of view.
  skill.removeAttribute('name');
  skill.dataset.expanded = String(skill.open);
  skill.closest('.skill-list').classList.add('is-animated');
  const summary = skill.querySelector('summary');
  // Respond to actual pointer movement, not headings sliding under a still cursor.
  summary.addEventListener('pointermove', event => {
    if (hoverSkills.matches && event.pointerType !== 'touch' && hoverTarget !== skill) {
      clearTimeout(hoverTimer);
      hoverTarget = skill;
      hoverTimer = setTimeout(() => openSkill(skill), 160);
    }
  });
  summary.addEventListener('pointerleave', () => {
    clearTimeout(hoverTimer);
    hoverTarget = null;
  });
  summary.addEventListener('click', event => {
    event.preventDefault();
    clearTimeout(hoverTimer);
    if (hoverSkills.matches && event.detail > 0) openSkill(skill);
    else if (skill.dataset.expanded === 'true') setSkill(skill, false);
    else openSkill(skill);
  });
}
// Designs share a group within their section; audit topics and logo projects
// share a group across their project page. Closing artwork still works as before.
const disclosureGroups = new Map();
for (const disclosure of document.querySelectorAll('.design-disclosure, .audit-disclosure, .logo-disclosure')) {
  const scope = disclosure.closest(disclosure.classList.contains('design-disclosure') ? '.case-section' : 'main');
  if (!scope) continue;
  if (!disclosureGroups.has(scope)) disclosureGroups.set(scope, []);
  disclosureGroups.get(scope).push(disclosure);
}
for (const group of disclosureGroups.values()) {
  for (const disclosure of group) {
    disclosure.addEventListener('toggle', () => {
      if (!disclosure.open) return;
      let closedSibling = false;
      for (const other of group) {
        if (other !== disclosure && other.open) {
          other.open = false;
          closedSibling = true;
        }
      }
      // A tall design closing above can move the newly opened control offscreen.
      if (closedSibling) {
        const summary = disclosure.querySelector('summary');
        const rect = summary.getBoundingClientRect();
        if (rect.top < header.getBoundingClientRect().bottom || rect.bottom > window.innerHeight) {
          summary.scrollIntoView({ block: 'center', behavior: 'instant' });
        }
      }
    });
  }
}
const dialog = document.querySelector('.image-dialog');
const viewerImage = dialog.querySelector('img');
let lastTrigger;
function collapseComparison(disclosure) {
  disclosure.open = false;
  const summary = disclosure.querySelector('summary');
  summary.focus({ preventScroll: true });
  summary.scrollIntoView({ block: 'start', behavior: 'instant' });
}
for (const button of document.querySelectorAll('.collapse-comparison')) {
  button.addEventListener('click', () => collapseComparison(button.closest('.audit-disclosure')));
}
// The entire expanded logo section closes back to its heading on click.
for (const section of document.querySelectorAll('.logo-project')) {
  const disclosure = section.querySelector('.logo-disclosure');
  section.addEventListener('click', event => {
    if (!disclosure.open || event.target.closest('summary')) return;
    if (window.getSelection()?.toString()) return;
    collapseComparison(disclosure);
  });
}
for (const preview of document.querySelectorAll('.device-preview')) {
  let start;
  let dragged = false;
  preview.addEventListener('pointerdown', event => {
    start = { x: event.clientX, y: event.clientY };
    dragged = false;
  });
  preview.addEventListener('pointermove', event => {
    if (start && Math.hypot(event.clientX - start.x, event.clientY - start.y) > 8) dragged = true;
  });
  preview.addEventListener('pointercancel', () => { dragged = true; start = null; });
  preview.addEventListener('click', () => {
    start = null;
    if (!dragged && !window.getSelection()?.toString()) {
      collapseComparison(preview.closest('.design-disclosure'));
    }
  });
  preview.addEventListener('keydown', event => {
    if (event.key === 'Escape' || event.key === 'Enter') {
      event.preventDefault();
      collapseComparison(preview.closest('.design-disclosure'));
    }
  });
}
for (const link of document.querySelectorAll('[data-lightbox]')) {
  const disclosure = link.closest('.design-disclosure, .audit-disclosure');
  if (disclosure) {
    link.setAttribute('role', 'button');
    link.setAttribute('aria-label', `Collapse design: ${link.querySelector('img').alt}`);
    link.title = 'Click to collapse design';
    link.addEventListener('keydown', event => {
      if (event.key === ' ') {
        event.preventDefault();
        link.click();
      }
    });
  }
  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (disclosure) {
      event.preventDefault();
      if (disclosure.classList.contains('audit-disclosure')) {
        collapseComparison(disclosure);
        return;
      }
      disclosure.open = false;
      const summary = disclosure.querySelector('summary');
      summary.focus({ preventScroll: true });
      const rect = summary.getBoundingClientRect();
      if (rect.top < header.getBoundingClientRect().bottom || rect.bottom > window.innerHeight) {
        summary.scrollIntoView({ block: 'center', behavior: 'instant' });
      }
      return;
    }
    if (typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    lastTrigger = link;
    viewerImage.src = link.href;
    viewerImage.alt = link.querySelector('img').alt;
    dialog.querySelector('.original-link').href = link.href;
    dialog.showModal();
    document.body.classList.add('viewer-open');
    dialog.querySelector('.viewer-scroll').scrollTop = 0;
    dialog.querySelector('.close-viewer').focus();
  });
}
dialog.querySelector('.close-viewer').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const rect = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
});
dialog.addEventListener('close', () => {
  document.body.classList.remove('viewer-open');
  viewerImage.removeAttribute('src');
  lastTrigger?.focus({ preventScroll: true });
});

// Muted previews start on arrival and pause offscreen or while a viewer is open.
const arrivalPreviews = [...document.querySelectorAll('[data-arrival-video]')];
const visiblePreviews = new Set();
function syncArrivalPreviews() {
  for (const link of arrivalPreviews) {
    const preview = link.querySelector('video');
    const shouldPlay = visiblePreviews.has(link) && !document.hidden &&
      !document.querySelector('.video-dialog[open]');
    if (shouldPlay) {
      preview.play().then(() => {
        if (visiblePreviews.has(link) && !document.hidden && !document.querySelector('.video-dialog[open]')) {
          link.classList.add('is-playing');
        } else {
          preview.pause();
          link.classList.remove('is-playing');
        }
      }).catch(() => link.classList.remove('is-playing'));
    } else {
      preview.pause();
      link.classList.remove('is-playing');
    }
  }
}
if ('IntersectionObserver' in window) {
  const arrivalObserver = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) visiblePreviews.add(entry.target);
      else visiblePreviews.delete(entry.target);
    }
    syncArrivalPreviews();
  }, { threshold: 0.15 });
  arrivalPreviews.forEach(link => arrivalObserver.observe(link));
}
document.addEventListener('visibilitychange', syncArrivalPreviews);
const videoDialog = document.querySelector('.video-dialog');
if (videoDialog) {
  const player = videoDialog.querySelector('video');
  const title = videoDialog.querySelector('#video-viewer-title');
  const errorMessage = videoDialog.querySelector('.video-error');
  let videoTrigger;
  for (const link of document.querySelectorAll('[data-video]')) {
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      if (typeof videoDialog.showModal !== 'function') return;
      event.preventDefault();
      videoTrigger = link;
      title.textContent = link.getAttribute('aria-label').replace(/^Play /, '');
      player.setAttribute('aria-label', title.textContent);
      errorMessage.hidden = true;
      videoDialog.querySelector('.video-download').href = link.href;
      player.src = link.href;
      videoDialog.showModal();
      syncArrivalPreviews();
      if (link.hasAttribute('data-fullscreen')) {
        if (videoDialog.requestFullscreen) {
          videoDialog.requestFullscreen().catch(() => {});
        } else if (player.webkitEnterFullscreen) {
          try { player.webkitEnterFullscreen(); } catch {}
        }
      }
      document.body.classList.add('viewer-open');
      videoDialog.querySelector('.close-viewer').focus();
      // Keep native controls usable if a browser declines automatic playback.
      player.play().catch(() => {});
    });
  }
  videoDialog.querySelector('.close-viewer').addEventListener('click', () => videoDialog.close());
  videoDialog.addEventListener('click', event => {
    if (event.target === videoDialog) videoDialog.close();
  });
  videoDialog.addEventListener('cancel', event => {
    event.preventDefault();
    videoDialog.close();
  });
  videoDialog.addEventListener('close', () => {
    if (document.fullscreenElement === videoDialog) {
      document.exitFullscreen().catch(() => {});
    }
    player.pause();
    player.removeAttribute('src');
    player.load();
    document.body.classList.remove('viewer-open');
    videoTrigger?.focus({ preventScroll: true });
    syncArrivalPreviews();
  });
  player.addEventListener('error', () => {
    if (videoDialog.open) errorMessage.hidden = false;
  });
}

// Match the reference's variable-height, stacked panel pinning on the homepage.
if (document.body.classList.contains('home')) {
  const folds = [...document.querySelectorAll('main > section')];
  const work = document.querySelector('#work');
  function fitOverview() {
    work.style.removeProperty('--overview-image-height');
    if (window.innerWidth <= 800) return;
    const grid = work.querySelector('.project-grid');
    const imageHeight = grid.querySelector('.card-image').getBoundingClientRect().height;
    const style = getComputedStyle(work);
    const outerHeight = element => {
      const computed = getComputedStyle(element);
      return element.getBoundingClientRect().height + parseFloat(computed.marginTop) + parseFloat(computed.marginBottom);
    };
    // Reserve the actual heading, title, gap and padding heights before sizing images.
    const fixedHeight = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
      + outerHeight(work.querySelector('.eyebrow')) + outerHeight(work.querySelector('h2'))
      + grid.getBoundingClientRect().height - 2 * imageHeight;
    const availableHeight = (window.innerHeight - headerHeight - fixedHeight - 12) / 2;
    work.style.setProperty('--overview-image-height', `${Math.max(1, Math.floor(Math.min(imageHeight, availableHeight)))}px`);
  }
  fitOverview();
  window.addEventListener('resize', fitOverview);
  document.fonts?.ready.then(fitOverview);
  if (window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);
    const motion = gsap.matchMedia();
    ScrollTrigger.addEventListener('refreshInit', fitOverview);
    ScrollTrigger.addEventListener('refresh', updateHeader);
    motion.add('(prefers-reduced-motion: no-preference)', () => {
      document.documentElement.classList.add('stacked-home');
      let navigating = false;
      let navigationTimer;
      const tops = folds.map(fold => ScrollTrigger.create({ trigger: fold, start: () => `top ${headerHeight}px` }));
      // Contact stays in normal flow: no pin at the end of the document.
      const pins = folds.map((fold, index) => index === folds.length - 1 ? null : ScrollTrigger.create({
        trigger: fold,
        start: () => fold.offsetHeight <= window.innerHeight - headerHeight ? `top ${headerHeight}px` : 'bottom bottom',
        pin: true,
        pinSpacing: false,
        invalidateOnRefresh: true
      }));
      ScrollTrigger.create({
        start: 0,
        end: () => ScrollTrigger.maxScroll(window),
        invalidateOnRefresh: true,
        // Run after panel pinning has updated, including during snap scrolling.
        onUpdate: updateHeader,
        snap: {
          snapTo(progress, self) {
            const y = self.scroll();
            // Once Contact arrives, leave its position alone, including on short screens.
            const contactStart = Math.min(ScrollTrigger.maxScroll(window), tops[tops.length - 1].start);
            if (y >= contactStart - 1) return progress;
            // Never pull visitors out of the middle of a tall mobile/text-expanded fold.
            if (navigating || folds.some((fold, i) => fold.offsetHeight > window.innerHeight - headerHeight + 2 && y > tops[i].start + 2 && y <= (pins[i]?.start ?? Infinity) + 2)) return progress;
            const maximum = ScrollTrigger.maxScroll(window);
            if (!maximum) return 0;
            const starts = tops.map(top => Math.min(maximum, top.start));
            const target = gsap.utils.snap(starts, y);
            return target / maximum;
          },
          duration: 0.5
        }
      });
      function navigate(event) {
        const link = event.target.closest('a[href^="#"]');
        if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        const index = folds.findIndex(fold => `#${fold.id}` === link.hash);
        if (index < 0) return;
        event.preventDefault();
        navigating = true;
        clearTimeout(navigationTimer);
        history.pushState(null, '', link.hash);
        window.scrollTo({ top: tops[index].start, behavior: 'smooth' });
        navigationTimer = setTimeout(() => { navigating = false; }, 1200);
      }
      document.addEventListener('click', navigate);
      document.fonts?.ready.then(() => ScrollTrigger.refresh());
      ScrollTrigger.refresh();
      const initialIndex = folds.findIndex(fold => `#${fold.id}` === location.hash);
      if (initialIndex >= 0) window.scrollTo({ top: tops[initialIndex].start, behavior: 'instant' });
      return () => {
        clearTimeout(navigationTimer);
        document.removeEventListener('click', navigate);
        document.documentElement.classList.remove('stacked-home');
      };
    });
  }
}

// Load the supplied inline scheduler only after the contact popup is visible.
const contactDialog = document.querySelector('.contact-dialog');
if (contactDialog) {
  let contactTrigger;
  let calendlyScript;
  const closeContact = contactDialog.querySelector('.close-contact');
  for (const link of document.querySelectorAll('[data-contact-popup]')) {
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      if (typeof contactDialog.showModal !== 'function') return;
      event.preventDefault();
      contactTrigger = mobileNavigation.matches ? navToggle : link;
      setNavigationOpen(false);
      contactDialog.showModal();
      document.body.classList.add('contact-open');
      contactDialog.querySelector('.contact-dialog-content').scrollTop = 0;
      closeContact.focus();
      if (!calendlyScript) {
        calendlyScript = document.createElement('script');
        calendlyScript.src = 'https://assets.calendly.com/assets/external/widget.js';
        calendlyScript.async = true;
        calendlyScript.onerror = () => {
          contactDialog.querySelector('.booking-error').hidden = false;
          calendlyScript.remove();
          calendlyScript = null;
        };
        document.head.append(calendlyScript);
      }
    });
  }
  closeContact.addEventListener('click', () => contactDialog.close());
  contactDialog.addEventListener('click', event => {
    const rect = contactDialog.getBoundingClientRect();
    if (event.target === contactDialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) contactDialog.close();
  });
  contactDialog.addEventListener('close', () => {
    document.body.classList.remove('contact-open');
    contactTrigger?.focus({ preventScroll: true });
  });
}
