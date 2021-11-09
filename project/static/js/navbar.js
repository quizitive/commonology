// --- use this function to register listeners --- //
$(function() {
  // close content elements by clicking anywhere
  $(document).bind("click", (event) => {
  showHideElement(event, "#navbar-dropdown-content");
  showHideElement(event, "#change-game-content");
  })
  // clicking triggering elements opens or closes
  $("#navbar-dropdown-icon").bind("click", (event) => {
    showHideElement(event,"#navbar-dropdown-content",true)
  });
  $("#change-game").bind("click", (event) => {
    showHideElement(event,"#change-game-content",true)
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