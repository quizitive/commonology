function filterFocus(elm) {
    $('div.filter-button').removeClass('cg-blue').addClass('w3-light-grey')
    $(elm).addClass("selected").addClass('cg-blue').removeClass('w3-light-grey')
}