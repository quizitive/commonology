$(() => {
  $('.chart').each((i, elm) => {
    console.log(elm.id)
    var ctx = elm.getContext('2d');
    var config = JSON.parse(JSON.parse(document.getElementById(elm.id + '-data').textContent));
    var myChart = new Chart(ctx, config);
  })
})

