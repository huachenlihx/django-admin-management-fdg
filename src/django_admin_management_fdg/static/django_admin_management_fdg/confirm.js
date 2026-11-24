document.addEventListener('click', (event) => {
  const link = event.target.closest?.('a[data-fdg-confirm]');
  if (link && !window.confirm(link.dataset.fdgConfirm)) event.preventDefault();
});
