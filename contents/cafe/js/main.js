// 営業日時設定
var time = new Date();
var month = time.getMonth() + 1;
var day = time.getDate();
var date = `${month}/${day}`;
var dateId = document.getElementById('date');
dateId.innerHTML = date;//日付設定

var weekNameId = document.getElementById('week');
var timeId = document.getElementById('time');
var week = time.getDay();
var weekName = ['日','月','火','水','木','金','土'];
weekNameId.innerHTML = weekName[week];//曜日設定

//営業時間設定
if(weekName[week] === "火"){
	timeId.innerHTML = "本日火曜日は定休日です。";
}else if(weekName[week] === "日"){
	timeId.innerHTML = "9:00～18:00(LO17:30)";
}else{
	timeId.innerHTML = "10:00～19:00(LO18:30)";
}

//OPENとCLOSE、画像の切り替え
function onTime(){
	setInterval(function(){
		var status = document.getElementById('status_img');
		status.style.setProperty("visibility", "visible");
		dateId.style.setProperty("visibility", "visible");
		weekNameId.style.setProperty("visibility", "visible");
		timeId.style.setProperty("visibility", "visible");
		var hour = time.getHours();
		var minute = time.getMinutes();
		var padHour = String(hour).padStart(2,'0');
		var padMinute = String(minute).padStart(2,'0');
		var now = `${padHour}${padMinute}`;

		if(weekName[week] === "火"){
			status.setAttribute("src", "./img/status_close.png");
		}else if(weekName[week] === "日" && now > 900 && now < 1800){
			status.setAttribute("src", "./img/status_open.png");
		}else if(now < 1000 || now > 1900){
			status.setAttribute("src", "./img/status_close.png");
		}else{
			status.setAttribute("src", "./img/status_open.png");
		}
	},100);
};
onTime();

//記事のNEW表示、自動切換
var year = time.getFullYear();
var padMonth = String(month).padStart(2,'0');
var padDay = String(day).padStart(2,'0');
var fullTime = `${year}${padMonth}${padDay}`;

var timeSevenDaysLater = new Date();
timeSevenDaysLater.setDate(timeSevenDaysLater.getDate() - 7);//削除までの日数
var daySevenLater = timeSevenDaysLater.getDate();
var padDaySevenLater = String(daySevenLater).padStart(2,'0');
var fullTimeSevenDayLater = Number(`${year}${padMonth}${padDaySevenLater}`);

var newSwitch = document.querySelectorAll('.new_container');
var newsDay = document.querySelectorAll('.news_day');
for(i = 0; i < newsDay.length; i++){
	var newsTime = Number(newsDay[i].textContent.replace(/\./g,''));
	if(newsTime < fullTimeSevenDayLater){
		newSwitch[i].classList.add('hiddenNewIcon');
	}else{
		newSwitch[i].classList.remove('hiddenNewIcon');
	}
}


//ナビの追従開始位置
$(function(){
var nav = $('nav');
var scrollPadding = $('#slider1');
var scrollPaddingLogo = $('#sliderAbsolute');
var navOffset = nav.offset().top;
function funcNav(){
	var winScroll = $(window).scrollTop();
	if(winScroll >= navOffset){
		nav.addClass('scroll');
		scrollPadding.addClass('padding');
		scrollPaddingLogo.addClass('padding');
		$('header').css('padding-top','0px');
		$('header > nav > ul > li.logo').css('display','none');
		$('header > nav > ul > li.status').css('display','none');
	}else{
		nav.removeClass('scroll');
		scrollPadding.removeClass('padding');
		scrollPaddingLogo.removeClass('padding');
		$('header').css('padding-top','10px');
		$('header > nav > ul > li.logo').css('display','');
		$('header > nav > ul > li.status').css('display','');
	}
}


window.addEventListener('load',funcNav);
window.addEventListener('scroll',funcNav);
});

//ナビ矢印の切り替わり
$(function(){
var arrowChange = document.querySelectorAll('.arrow');
var arrowTriggerMargin = 480;
var arrowMenu = document.querySelectorAll('li.menu > ul > li');
var arrow = $('li.menu > ul > li');
var funcArrow = function(){
	for(i = 0; i < arrowChange.length; i++){
 if(window.innerHeight > arrowChange[4].getBoundingClientRect().top + arrowTriggerMargin){
 	arrowMenu[4].classList.add('cursor');
 	arrowMenu[3].classList.remove('cursor');
 	arrowMenu[2].classList.remove('cursor');
 	arrowMenu[1].classList.remove('cursor');
 	arrowMenu[0].classList.remove('cursor');
	}else if(window.innerHeight > arrowChange[3].getBoundingClientRect().top + arrowTriggerMargin){
	arrowMenu[3].classList.add('cursor');
	arrowMenu[4].classList.remove('cursor');
 	arrowMenu[2].classList.remove('cursor');
 	arrowMenu[1].classList.remove('cursor');
 	arrowMenu[0].classList.remove('cursor');
	}else if(window.innerHeight > arrowChange[2].getBoundingClientRect().top + arrowTriggerMargin){
	arrowMenu[2].classList.add('cursor');
	arrowMenu[4].classList.remove('cursor');
 	arrowMenu[3].classList.remove('cursor');
 	arrowMenu[1].classList.remove('cursor');
 	arrowMenu[0].classList.remove('cursor');
	}else if(window.innerHeight > arrowChange[1].getBoundingClientRect().top + arrowTriggerMargin){
	arrowMenu[1].classList.add('cursor');
	arrowMenu[4].classList.remove('cursor');
 	arrowMenu[3].classList.remove('cursor');
 	arrowMenu[2].classList.remove('cursor');
 	arrowMenu[0].classList.remove('cursor');
	}else{
	arrowMenu[0].classList.add('cursor');
	arrowMenu[1].classList.remove('cursor');
	arrowMenu[2].classList.remove('cursor');
	arrowMenu[3].classList.remove('cursor');
	arrowMenu[4].classList.remove('cursor');
	};
};
};
window.addEventListener('load',funcArrow);
window.addEventListener('scroll',funcArrow);
});

//スライダー上の画像と説明文
$(function(){
	$('#sliderAbsolute').delay(100).fadeIn('.sliderTitleShow');
	setInterval(function(){
		$('#sliderAbsolute > h1').css({transform: "rotateY(360deg)"});
	},100);	
});

// MENUとINFOを回転させて表示
$(function(){
	var scrollAnim = document.querySelectorAll('.raise');
	var figure = document.querySelectorAll('.fig_show');
	var triggerMargin = 520;
	var funcShow = function(){
	for(i = 0; i < scrollAnim.length; i++){
 if(window.innerHeight > scrollAnim[i].getBoundingClientRect().top + triggerMargin){
	scrollAnim[i].classList.add('show');
	figure[i].classList.add('show')
	}
};
};

window.addEventListener('load',funcShow);
window.addEventListener('scroll',funcShow)


});

//その他フワッと表示

$(function(){
	var scrollAnimSub = document.querySelectorAll('.up');
	var triggerMargin = 200;
	var funcUp = function(){
	for(i = 0; i < scrollAnimSub.length; i++){
 if(window.innerHeight > scrollAnimSub[i].getBoundingClientRect().top + triggerMargin){
	scrollAnimSub[i].classList.add('showUp');
	}
};
};

window.addEventListener('load',funcUp);
window.addEventListener('scroll',funcUp)


});




//スムーズスクロール
$(function(){
   // #で始まるアンカーをクリックした場合に処理
   $('a[href^=#]').click(function() {
      // スクロールの速度
      var speed = 400; // ミリ秒
      // アンカーの値取得
      var href= $(this).attr("href");
      // 移動先を取得
      var target = $(href == "#" || href == "" ? 'html' : href);
      // 移動先を数値で取得
      var position = target.offset().top;
      // スムーススクロール
      $('body,html').animate({scrollTop:position}, speed, 'swing');
      return false;
   });
});


//トップのスライダー
  $(document).ready(function($){
        $('#slider1').sliderPro({
        width: "1000px",
        height: "600px",
        centerImage: true,
        responsive: true,
        slideDistance: 0,
        visibleSize: "100%",
        fadeDuration: 1500,
        buttons: false,
  });
  });

//ページトップ
$(function() {
    var topBtn = $('#page-top');    
    topBtn.hide();
    //スクロールが100に達したらボタン表示
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            topBtn.fadeIn();
        } else {
            topBtn.fadeOut();
        }
    });
    //スクロールしてトップ
    topBtn.click(function () {
        $('body,html').animate({
            scrollTop: 0
        }, 500);
        return false;
    });
});

//ハンバーガーメニュー
$('.rwdMenuBlock').on('click',function(){
	$('.rwdMenu01,.rwdMenu02,.rwdMenu03').toggleClass('onClick');

	$('.gnavArea').animate({height:'toggle'},'middle');
});

$(window).on('load resize',function(){
var w = $(window).width();
var o = 1000;
if(w >= o){
	$('.gnavArea').css('display','none');
}
});
