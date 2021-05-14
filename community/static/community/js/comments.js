$('.comment-text').bind('change keyup paste testing', (e) => {
  const button_id = '#post_'.concat(e.target.id.split('_')[1])
  console.log('received testing')
  if ($(e.target).val() === "") {
    $(button_id).attr('disabled', true);
  } else {
    $(button_id).attr('disabled', false);
  }
});


function isScrolledIntoView(elem)
{
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();

    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}

$.fn.isInViewport = function () {
    let elementTop = $(this).offset().top;
    let elementBottom = elementTop + $(this).outerHeight();

    let viewportTop = $(window).scrollTop();
    let viewportBottom = viewportTop + $(window).height();

    return elementBottom > viewportTop && elementTop < viewportBottom;
};

$(window).scroll(function(e){
  $(".question-comment-container").each(function() {
    if ($(this).isInViewport()) {
      console.log(this.id)
    }
  })
})

