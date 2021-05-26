// show and hide extra answers/comments (hide may not work)
$(".more-button, .show-comments").click((event) => {
  const objTypeId = event.target.id.split(" ")[1].split("-")
  const tgtClass = "." + objTypeId[0] + "-" + objTypeId[1] + ".hideable"
  $(tgtClass).toggle().toggleClass("is_hidden");
  $(event.target).text("")
})

$(".question-comments").on("htmx:load", (event) => {
  // hide the oldest visible comment
  const $commentToHide = $(event.target).siblings(".question-comment").not(".hideable").first()
  $commentToHide.addClass("hideable").toggle()

  // update hidden comment count
  var totalComments = parseInt($(event.target).siblings("a").text().split(" ")[2]) + 1
  $(event.target).siblings("a").text("View all " + totalComments + " comments")
})

// $('.question-comments').on("htmx:beforeProcessNode", (e) => {
//   // const text_area_id = '#text-'.concat(e.target.id.split('-')[1])
//   // $(text_area_id).val('');
//   var $x = $('textarea');
//   var $next = $x.eq($x.index(this) + 1);
//   $next.val("")
// });
