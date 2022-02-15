// --- Clickable Choices --- //
$clickableChoices = $('.w3-cell-row.response-item')
$clickableChoices.click((e) => {
  // add the value of the selection to the hidden input
  $(e.currentTarget).siblings('input[name=raw_string]').val($(e.currentTarget).find('.choice').text())
  // add border from player-answer formatting
  $(e.currentTarget).addClass('player-answer').siblings('.player-answer').removeClass('player-answer').find('i').css('display', 'none')
  // add checkmark
  $(e.currentTarget).find("i").css('display', 'block')

  removeErrors(e)
})
// allow pressing enter as mouse click
$clickableChoices.keydown(function(e){
    if(e.which === 13){
        $(this).click();
    }
});

// Enter text in text box removes errors
const $textInputQuestions = $("input[name=raw_string][required], input[name=display_name]")
$textInputQuestions.on('change keypress keyup paste', (e) => {
  removeErrors(e)
})

function removeErrors(e) {
  $(e.currentTarget).closest(".question-container").css("border-color", "#cecece")
  $(e.currentTarget).siblings(".errors").html('')
}

// --- Question Validation --- //
$('#submit-button').click((e) => {
  // don't submit form yet
  e.preventDefault()

  // check all inputs for a value
  var errors = false
  var scrollTop = 0
  $textInputQuestions.each((i, elm) => {
    if ($(elm).val().trim() === "") {
      $(elm).closest(".question-container").css("border-color", "#ec1c24")
      $(elm).next(".errors").html('<ul class="errorlist"><li>This is a required question</li></ul>')
      errors = true
      if (scrollTop === 0) {
        scrollTop = $(elm).closest('.question-container').offset().top
      }
    }
  })
  if (!errors) {
    $("#game_form").submit();
  } else {
    // scroll to topmost element with some buffer for the navbar
    $([document.documentElement, document.body]).animate({scrollTop: scrollTop - 75}, 500);
  }

})