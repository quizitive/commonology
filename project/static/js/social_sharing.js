$(function() {
  // Bind share functionality to #share-button.
  // Mobile devices attempt to open native share dialogue, fallthrough to copy-to-clipboard.
  // see: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share
  // Desktops just copy to clipboard because most people don't have apps installed and poor browser support.
  $("#share-button").bind('click', async () => {
    // Define share content. Must have link on page at id #share-link
    const shareMsg = JSON.parse($("#share-msg").text())["message"];
    const filesArray = [];
    if (mobileAndTabletCheck()) {
      // It's a mobile device
      await sharePlayLink(shareMsg, filesArray);
    } else {
      // It's a desktop device
      // todo: make a share widget with
      setClipboard(shareMsg);
    }
  });
})

async function sharePlayLink(shareMsg, filesArray) {
  let shareData = {
        files: filesArray,
        title: "Let's play Commonology!",
        text: shareMsg,
      }

   try {
      await navigator.share(shareData)
    } catch(err) {
      if (err instanceof TypeError) {
        // This device doesn't support sharing files.
        console.log(`Your system doesn't support sharing files. Copying to clipboard`);
        setClipboard(shareMsg);
      } else {
        console.log('Error: ' + err)
      }
    }
}

function shareMyResults(displayName) {
    let div = document.getElementById('my-results-sharable')
    html2canvas(div, {
      onclone: function(clone) {
        $(clone).find("#welcome-container").addClass("w3-center")
        $(clone).find("#all-stat-container").css({"padding": 0, "margin": "auto", "width": "250px"})
        $(clone).find("#welcome-message")
          .text("Game 84 results for " + displayName)
          .css({"width": "100%"})
        $(clone).find("#my-results-sharable").show()
      }
    }).then(
        function (canvas) {
          $(canvas).prepend("Check out my results on Commonology this week!")
          canvas.toBlob(function(blob) {
            const item = new ClipboardItem({ "image/png": blob });
            navigator.clipboard.write([item]);
          });
            $("#copy-msg").show();
        })
}

function setClipboard(text) {
    var type = "text/plain";
    var blob = new Blob([text], { type });
    var data = [new ClipboardItem({ [type]: blob })];

    navigator.clipboard.write(data).then(
        function () {
        console.log("Copied to clipboard")
        $("#copy-msg").css("display", "inline");
        },
        function () {
        console.log("Failed to copy to clipboard")
        }
    );
}

// Check for mobile
window.mobileAndTabletCheck = function() {
  let check = false;
  (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|android|ipad|playbook|silk/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
  return check;
};

jQuery.fn.resizeHeightMaintainRatio = function(newHeight){
    var aspectRatio = $(this).data('aspectRatio');
    if (aspectRatio == undefined) {
        aspectRatio = $(this).width() / $(this).height();
        $(this).data('aspectRatio', aspectRatio);
    }
    $(this).height(newHeight);
    $(this).width(parseInt(newHeight * aspectRatio));
}