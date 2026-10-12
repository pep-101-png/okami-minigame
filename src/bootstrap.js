// Keep a visible loading/error screen even when importing the game fails.
try {
  await import('./main.js');
  document.querySelector('#boot').style.display = 'none';
} catch (error) {
  console.error(error);
  window.showGameError(error.message.includes('WebGL')
    ? '3D rendering is unavailable in this browser. Enable hardware acceleration and use a browser with WebGL 2 support, then reload.'
    : `The game could not load: ${error.message}. Refresh the page to retry.`);
}
