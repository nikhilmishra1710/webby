var count = 0;
function callback() {
  console.log("callback function called");
  var output = document.querySelectorAll("div")[1];
  output.innerHTML = "count: " + count++;
  if (count < 100) {
    console.log("callback function re - registered");
    requestAnimationFrame(callback);
  }
}
console.log("callback function registered");
requestAnimationFrame(callback);

undefined;
