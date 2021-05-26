// enable post button when content is entered
$('.comment-text').on('change keyup paste testing', (e) => {
  const button_id = '#post-'.concat(e.target.id.split('-')[1])
  if ($(e.target).val() === "") {
    $(button_id).attr('disabled', true);
  } else {
    $(button_id).attr('disabled', false);
  }
});

// clear textarea value when post button is clicked
$('.question-comments').on("htmx:beforeProcessNode", (e) => {
  const text_area_id = '#text-'.concat(e.target.id.split('-')[1])
  $(text_area_id).val('');
});
htmx.logAll();
