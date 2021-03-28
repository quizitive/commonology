window.onload = function () {
  document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
  })
  document.body.addEventListener('htmx:responseError', (event) => {
    if (event.detail.error.search("Error Code 403") !== -1) {
      loginPrompt();
    }
  })
}

// Handle 403
function loginPrompt() {
  document.getElementById('login-modal').style.display='block';
}