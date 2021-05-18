$('.comment-text').bind('change keyup paste testing', (e) => {
  const button_id = '#post-'.concat(e.target.id.split('-')[1])
  console.log('received testing')
  if ($(e.target).val() === "") {
    $(button_id).attr('disabled', true);
  } else {
    $(button_id).attr('disabled', false);
  }
});

const roomName = JSON.parse(document.getElementById('room-name').textContent);

// const chatSocket = new WebSocket(
//     'ws://'
//     + window.location.host
//     + '/ws/chat/'
//     + 'lobby'
//     + '/'
// );

// chatSocket.onmessage = function(e) {
//     const data = JSON.parse(e.data);
//     document.querySelector('#chat-log').value += (data.message + '\n');
// };

// chatSocket.onclose = function(e) {
//     console.error('Chat socket closed unexpectedly');
// };

// document.querySelector('#chat-message-input').focus();
// document.querySelector('#chat-message-input').onkeyup = function(e) {
//     if (e.keyCode === 13) {  // enter, return
//         document.querySelector('#chat-message-submit').click();
//     }
// };

$('.post-button').click(function(e) {
  const text_area_id = '#text-'.concat(e.target.id.split('-')[1])
  // const message = $(text_area_id).val()
  // chatSocket.send(JSON.stringify({
  //   'message': message
  // }));
  // $(text_area_id).val('');
});