document.querySelectorAll('[data-view]').forEach(button => {
 button.addEventListener('click', () => {
  const selected = button.dataset.view;
  document.querySelectorAll('[data-view]').forEach(item => {
   const active = item.dataset.view === selected;
   item.classList.toggle('active', active);
   item.setAttribute('aria-pressed', String(active));
  });
  document.querySelector('#dashboard-view').hidden = selected !== 'dashboard';
  document.querySelector('#explanation-view').hidden = selected !== 'explanation';
 });
});
