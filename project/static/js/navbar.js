// --- use this function to register listeners --- //
$(function() {
  // click anywhere closes dropdown
    $(document).bind("click", (event) => {
    showHideElement(event, "#navbar-dropdown-content")
  })
  // clicking on caret can open or close dropdown
  $("#navbar-dropdown-icon").bind("click", (event) => {
    showHideElement(event,"#navbar-dropdown-content",true)
  });
})

// --- define listener functionality ---- //
function showHideElement(e, elem, canOpen=false) {
  const drpdn = $(elem)
  if (!drpdn.hasClass("w3-show") && canOpen === true) {
    drpdn.addClass("w3-show").removeClass("w3-hide")
    e.stopPropagation()
  } else {
    drpdn.removeClass("w3-show")
  }
}