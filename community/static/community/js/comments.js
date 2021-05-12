$('.comment-text').bind('change keyup paste', (e) => {
  const button_id = '#post-'.concat(e.target.id.split('-')[1])
  if ($(e.target).val() === "") {
    $(button_id).attr('disabled', true);
  } else {
    $(button_id).attr('disabled', false);
  }
});

