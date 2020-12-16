//フワッと表示
	window.onload = function onLoad(){
		//リボン、タイマー制御
		setInterval(() => {
		const float = document.querySelector('.ribbon');
		const float_b = document.querySelector('.timer');
		float.classList.add('float');
		float_b.classList.add('float');
	},500);
		onLoad_b();
};

	function onLoad_b(){
		//雲制御
		setInterval(() => {
		const float_clowd_l = document.querySelector('.clowd_left');
		const float_clowd_r = document.querySelector('.clowd_right');
		float_clowd_l.classList.add('float');
		float_clowd_r.classList.add('float');
	},1000);
};

//カウントダウンタイマー
setInterval(() => {
	var date = new Date();
	var reiwaDate = new Date('2019/05/01 00:00:00');
	var period = reiwaDate - date;

	if(period >= 0){
		var day = Math.floor(period / (1000 * 60 * 60 * 24));
		period -= (day *(1000 * 60 * 60 * 24));
		var hour = Math.floor(period / (1000 * 60 * 60));
		period -= (hour *(1000 * 60 * 60));
		var minute = Math.floor(period / (1000 * 60));
		period -= (minute *(1000 * 60));
		var second = Math.floor(period / 1000);

		document.querySelector('.day_time').innerHTML = String(day).padStart(2,'0');
		document.querySelector('.hour_time').innerHTML = String(hour).padStart(2,'0');
		document.querySelector('.minute_time').innerHTML = String(minute).padStart(2,'0');
		document.querySelector('.second_time').innerHTML = String(second).padStart(2,'0');
	}
	},20);
