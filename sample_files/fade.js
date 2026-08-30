var div = document.querySelectorAll("div")[0];
var total_frames = 120;
var current_frame = 0;
var change_per_frame = (0.999 - 0.1) / total_frames;
var base_opacity = 0.1;
function animate() {
  current_frame++;
  var new_opacity = current_frame * change_per_frame + base_opacity;
  div.style = "opacity:" + new_opacity;
  console.log(current_frame < total_frames);
  return current_frame < total_frames;
}

var fade_in = document.querySelectorAll("button")[0];
var fade_out = document.querySelectorAll("button")[1];

function run_animation_frame() {
  if (animate()) requestAnimationFrame(run_animation_frame);
}

fade_in.addEventListener("click", () => {
  change_per_frame = (0.999 - 0.1) / total_frames;
  current_frame = 0;
  base_opacity = 0.1;
  requestAnimationFrame(run_animation_frame);
});

fade_out.addEventListener("click", () => {
  change_per_frame = -(0.999 - 0.1) / total_frames;
  current_frame = 0;
  base_opacity = 0.99;
  requestAnimationFrame(run_animation_frame);
});
