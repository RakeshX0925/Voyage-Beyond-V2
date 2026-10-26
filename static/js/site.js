document.addEventListener('DOMContentLoaded', () => {
  // Close the mobile menu after choosing a destination.
  const nav = document.querySelector('.app-links');
  const toggle = document.querySelector('.nav-toggle');
  toggle?.setAttribute('aria-expanded', 'false');
  toggle?.addEventListener('click', () => {
    const isOpen = nav?.classList.toggle('open') ?? false;
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
  document.querySelectorAll('.app-links a').forEach(link => link.addEventListener('click', () => {
    nav?.classList.remove('open');
    toggle?.setAttribute('aria-expanded', 'false');
  }));
  // Allow the gallery lightbox to close with Escape.
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const lightbox = document.getElementById('lightbox');
      if (lightbox) lightbox.style.display = 'none';
    }
  });
});
