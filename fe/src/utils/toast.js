export function showToast(message, type = 'success', duration = 2500) {
  window.dispatchEvent(
    new CustomEvent('show-toast', {
      detail: { message, type, duration },
    }),
  );
}
