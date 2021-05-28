const visibleComments = JSON.parse(document.getElementById('visible-comments').textContent);

// enable post button when content is entered
$('.comment-text').on('change keyup paste testing', (e) => {
  togglePostButton(e)
});

// clear textarea value when post button is clicked
$('.question-comments').on("htmx:beforeProcessNode", (e) => {
  const text_area_id = '#text-'.concat(e.target.id.split('-')[1])
  $(text_area_id).val('');
});

// show and hide extra answers/comments (hide may not work)
$(".more-button, .show-comments").click((event) => {
  const objTypeId = event.target.id.split(" ")[1].split("-")
  const tgtClass = "." + objTypeId[0] + "-" + objTypeId[1] + ".hideable"
  $(tgtClass).toggle().toggleClass("is_hidden");
  $(event.target).text("")
})

// actions when comment is propagated to browser
$(".question-comments").on("htmx:load", (e) => {

  togglePostButton(e)

  if ($(e.target).siblings(".question-comment").length < visibleComments) {
    return;
  }

  // old comment hide logic
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
