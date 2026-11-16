// Progressive enhancement: the article and navigation also work without JavaScript.
const printButton = document.querySelector('[data-print]');
if (printButton) {
  printButton.hidden = false;
  printButton.addEventListener('click', () => window.print());
}
const copyButton = document.querySelector('[data-copy-citation]');
if (copyButton) {
  const citation = document.querySelector('#article-bibtex');
  const status = document.querySelector('.copy-status');
  const originalLabel = copyButton.textContent;
  let resetLabel;
  copyButton.hidden = false;
  copyButton.addEventListener('click', async () => {
    clearTimeout(resetLabel);
    try {
      await navigator.clipboard.writeText(citation.textContent);
      copyButton.textContent = copyButton.dataset.copied;
      status.textContent = copyButton.dataset.success;
    } catch {
      const range = document.createRange();
      range.selectNodeContents(citation);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = copyButton.dataset.failure;
    }
    resetLabel = setTimeout(() => { copyButton.textContent = originalLabel; }, 2500);
  });
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
