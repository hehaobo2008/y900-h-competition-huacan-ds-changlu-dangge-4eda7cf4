// Catch both WebGL initialization and required-asset failures.
import('./main.js').then(module => module.ready).catch(error => {
  console.error('Unable to open the scroll:', error);
  window.__error = error.message;
  document.getElementById('loading').classList.add('hidden');
  const screen = document.getElementById('errorScreen');
  screen.classList.remove('hidden'); screen.inert = false;
  document.getElementById('retryBtn').focus();
});
document.getElementById('retryBtn').addEventListener('click', () => location.reload());
