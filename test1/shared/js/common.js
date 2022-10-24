var clickEventType = ((window.ontouchstart !== null)?'click':'touchstart');

document.addEventListener("DOMContentLoaded", function(){
  //ハンバーガーメニュー
  const navBtn = document.getElementById("navBtn_js");
  const navBtnTarget = document.getElementById("navBtnTarget_js");
  navBtn.addEventListener(clickEventType, function(){
    this.classList.toggle("active");
    navBtnTarget.classList.toggle("active");
  }, false);
});