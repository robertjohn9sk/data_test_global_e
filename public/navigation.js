function connectViews(buttonSelector, panelSuffix) {
 const buttons = document.querySelectorAll(buttonSelector);
 const attribute = panelSuffix === 'view' ? 'view' : 'stage';
 buttons.forEach(button => button.addEventListener('click', () => {
  const selected = button.dataset[attribute];
  buttons.forEach(item => {
   const active = item.dataset[attribute] === selected;
   item.classList.toggle('active', active);
   item.setAttribute('aria-pressed', String(active));
   document.getElementById(item.dataset[attribute] + '-' + panelSuffix).hidden = !active;
  });
 }));
}
connectViews('[data-view]', 'view');
connectViews('[data-stage]', 'stage');
