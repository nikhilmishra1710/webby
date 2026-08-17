var allow_submit = true;
var strong = document.querySelectorAll("strong")[0];

function lengthCheck() {
  var value = this.getAttribute("value");
  allow_submit = value.length <= 10;
  if (!allow_submit) {
    strong.innerHTML = "Comment too long!";
  }
}

var inputs = document.querySelectorAll("input");
for (var i = 0; i < inputs.length; i++) {
  inputs[i].addEventListener("keydown", lengthCheck);
}

var form = document.querySelectorAll("form")[0];
form.addEventListener("submit", function (e) {
  console.log("Form submission started");
  if (!allow_submit) {
    e.preventDefault();
    console.log("Form submission stopped");
  }
  console.log("Form submission going for default behavior");
});
