// --- Clickable Choices --- //
$('.w3-cell-row.response-item').click((e) => {
  // add the value of the selection to the hidden input
  $(e.currentTarget).siblings('input[name=raw_string]').val($(e.currentTarget).find('.choice').text())
  // add border from player-answer formatting
  $(e.currentTarget).addClass('player-answer').siblings('.player-answer').removeClass('player-answer').find('i').css('display', 'none')
  // add checkmark
  $(e.currentTarget).find("i").css('display', 'block')

  removeErrors(e)
})
// todo:

// Enter text in text box removes errors
$('input[name=raw_string]').on('change keypress keyup paste', (e) => {
  removeErrors(e)
})

function removeErrors(e) {
  $(e.currentTarget).closest(".question-container").css("border-color", "#cecece")
  $(e.currentTarget).siblings(".errors").html('')
}

// --- Question Validation --- //
$('button[type=submit]').click((e) => {
  // don't submit form yet
  e.preventDefault()

  // check all inputs for a value
  var errors = false
  $("input[name=raw_string][required]").not("[value]").each((i, elm) => {
    if ($(elm).val() === "") {
      $(elm).closest(".question-container").css("border-color", "#ec1c24")
      $(elm).next(".errors").html('<ul class="errorlist"><li>This is a required question</li></ul>')
      errors = true
    //  todo: scroll to first error
    }
  })
  if (!errors) {
    $("form").submit();
  }
})