// --- Click Choices --- //
// todo: this

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
    }
  })

  if (!errors) {
    $("form").submit();
  }

})