export function requestPointer(canvas) {
  // Sandboxed embedded browsers may deny pointer lock. Keyboard gameplay
  // and a drag-to-look camera must remain usable in that case.
  try {
    const result = canvas.requestPointerLock?.();
    result?.catch(() => {});
  } catch {
    /* Drag-to-look remains available. */
  }
}
