const visibleComments = JSON.parse(document.getElementById('visible-comments').textContent);
const userName = JSON.parse(document.getElementById('user-name').textContent);

// enable post button when content is entered
$('.comment-text').on('change keypress keyup paste', (e) => {

  togglePostButton(e)

  // submit on enter
  if (e.which === 13) {
    e.preventDefault()
    const button_id = '#post-'.concat(e.target.id.split('-')[1])
    $(button_id).click();
  }
});

// clear textarea value when post button is clicked
$('.question-comment-form').submit((e) => {
  // show login prompt if user isn't logged in
  if (userName === "") {loginPrompt();return;}
  $(e.target).find("textarea").val("")
  togglePostButton(e)
});

// show and hide extra answers/comments (hide may not work)
$(".more-button, .show-comments").click((event) => {
  const objTypeId = event.target.id.split(" ")[1].split("-")
  const tgtClass = "." + objTypeId[0] + "-" + objTypeId[1] + ".hideable"
  $(tgtClass).toggle().toggleClass("is_hidden");
  $(event.target).text("").addClass("expanded")
})

// actions when comment is propagated to browser
$(".question-comments").on("htmx:load", (e) => {

  // don't toggle if view is already expanded
  if ($(e.target).siblings(".show-comments").hasClass("expanded")) {return;}

  // there aren't enough comments to do any hiding
  if ($(e.target).siblings(".question-comment").length < visibleComments) {return;}

  // hide oldest comment
  $(e.target).siblings(".show-comments").show()
  const $commentToHide = $(e.target).siblings(".question-comment").not(".hideable").first()
  $commentToHide.addClass("hideable").toggle()

  // update hidden comment count
  var totalComments = $(e.target).siblings(".question-comment").length + 1
  $(e.target).siblings("a").text("View all " + totalComments + " comments")
})

function togglePostButton(e) {
  const button_id = '#post-'.concat(e.target.id.split('-')[1])
  if ($(e.target).val().trim() === "") {
    $(button_id).attr('disabled', true);
  } else {
    $(button_id).attr('disabled', false);
  }
}
