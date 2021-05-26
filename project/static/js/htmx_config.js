$(function () {
  document.body.addEventListener('htmx:responseError', (event) => {
    if (event.detail.error.search("Error Code 401") !== -1) {
      loginPrompt();
    }
    if (event.detail.error.search("Error Code 403") !== -1) {
      // if we receive a 403 response from our own HTMX calls,
      // it could be CSRF failure, try reloading the page to log user in
      location.reload();
    }
  })
});

// Handle 403
function loginPrompt() {
  document.getElementById('login-modal').style.display='block';
}