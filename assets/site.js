// Progressive enhancement: the article and navigation also work without JavaScript.
const printButton = document.querySelector('[data-print]');
if (printButton) {
  printButton.hidden = false;
  printButton.addEventListener('click', () => window.print());
}
const headings = document.querySelectorAll('.article-body h2[id]');
const links = [...document.querySelectorAll('.toc a')];
if ('IntersectionObserver' in window && headings.length) {
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting);
    if (!visible.length) return;
    const active = '#' + visible[0].target.id;
    links.forEach(link => {
      if (decodeURIComponent(link.hash) === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }, { rootMargin: '-10% 0px -60% 0px' });
  headings.forEach(heading => observer.observe(heading));
}
