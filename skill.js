
$(function () {

var unit = 100,
    canvas, context, canvas2, context2,
    height, width, xAxis, yAxis, draw,
    canvas_b, context_b, canvas2_b, context2_b,
    height_b, width_b, xAxis_b, yAxis_b, draw_b,
    canvas_c, context_c, canvas2_c, context2_c,
    height_c, width_c, xAxis_c, yAxis_c, draw_c,
    canvas_d, context_d, canvas2_d, context2_d,
    height_d, width_d, xAxis_d, yAxis_d, draw_d,
    canvas_e, context_e, canvas2_e, context2_e,
    height_e, width_e, xAxis_e, yAxis_e, draw_e,
    canvas_f, context_f, canvas2_f, context2_f,
    height_f, width_f, xAxis_f, yAxis_f, draw_f,
    canvas_g, context_g, canvas2_g, context2_g,
    height_g, width_g, xAxis_g, yAxis_g, draw_g;


/**
 * Init function.
 * 
 * Initialize variables and begin the animation.
 */
function init() {
    
    canvas = document.getElementById("skill-html-css");
    canvas_b = document.getElementById("skill-photoshop");
    canvas_c = document.getElementById("skill-illustrator");
    canvas_d = document.getElementById("skill-jquery");
    canvas_e = document.getElementById("skill-javascript");
    canvas_f = document.getElementById("skill-wordpress");
    canvas_g = document.getElementById("skill-php");
    
    canvas.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas.height = 200;
    canvas_b.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_b.height = 200;
    canvas_c.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_c.height = 200;
    canvas_d.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_d.height = 400;
    canvas_e.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_e.height = 400;
    canvas_f.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_f.height = 400;
    canvas_g.width = document.documentElement.clientWidth; //Canvasのwidthをウィンドウの幅に合わせる
    canvas_g.height = 400;


    context = canvas.getContext("2d");
    context_b = canvas_b.getContext("2d");
    context_c = canvas_c.getContext("2d");
    context_d = canvas_d.getContext("2d");
    context_e = canvas_e.getContext("2d");
    context_f = canvas_f.getContext("2d");
    context_g = canvas_g.getContext("2d");

    height = canvas.height;
    width = canvas.width;
    height_b = canvas_b.height;
    width_b = canvas_b.width;
    height_c = canvas_c.height;
    width_c = canvas_c.width;
    height_d = canvas_d.height;
    width_d = canvas_d.width;
    height_e = canvas_e.height;
    width_e = canvas_e.width;
    height_f = canvas_f.height;
    width_f = canvas_f.width;
    height_g = canvas_g.height;
    width_g = canvas_g.width;
    
    xAxis = Math.floor(height/4.5);
    yAxis = 0;
    xAxis_b = Math.floor(height_b/2.5);
    yAxis_b = 0;
    xAxis_c = Math.floor(height_c/1.9);
    yAxis_c = 0;
    xAxis_d = Math.floor(height_d/2.1);
    yAxis_d = 0;
    xAxis_e = Math.floor(height_e/1.5);
    yAxis_e = 0;
    xAxis_f = Math.floor(height_f/1.3);
    yAxis_f = 0;
    xAxis_g = Math.floor(height_g/1.15);
    yAxis_g = 0;
    
    draw();
}

/**
 * Draw animation function.
 * 
 * This function draws one frame of the animation, waits 20ms, and then calls
 * itself again.
 */
function draw() {
    
    // キャンバスの描画をクリア
    context.clearRect(0, 0, width, height);
    context_b.clearRect(0, 0, width_b, height_b);
    context_c.clearRect(0, 0, width_c, height_c);
    context_d.clearRect(0, 0, width_d, height_d);
    context_e.clearRect(0, 0, width_e, height_e);
    context_f.clearRect(0, 0, width_f, height_f);
    context_g.clearRect(0, 0, width_g, height_g);


    //波を描画
    drawWave('rgba(255,255,255,0.2)', 1, 4, 0);
    drawWave('rgba(255,255,255,0.2)', 1, 4, 5);
    
    // Update the time and draw again
    draw.seconds = draw.seconds + .015;
    draw.t = draw.seconds*Math.PI;
    setTimeout(draw, 35);
};
draw.seconds = 0;
draw.t = 0;

/**
* 波を描画
* drawWave(色, 不透明度, 波の幅のzoom, 波の開始位置の遅れ)
*/
function drawWave(color, alpha, zoom, delay) {
    context.fillStyle = color;
    context.globalAlpha = alpha;
    context_b.fillStyle = color;
    context_b.globalAlpha = alpha;
    context_c.fillStyle = color;
    context_c.globalAlpha = alpha;
    context_d.fillStyle = color;
    context_d.globalAlpha = alpha;
    context_e.fillStyle = color;
    context_e.globalAlpha = alpha;
    context_f.fillStyle = color;
    context_f.globalAlpha = alpha;
    context_g.fillStyle = color;
    context_g.globalAlpha = alpha;

    context.beginPath(); //パスの開始
    context_b.beginPath(); //パスの開始
    context_c.beginPath(); //パスの開始
    context_d.beginPath(); //パスの開始
    context_e.beginPath(); //パスの開始
    context_f.beginPath(); //パスの開始
    context_g.beginPath(); //パスの開始
    drawSine(draw.t / 0.5, zoom, delay);
    context.lineTo(width + 10, height); //パスをCanvasの右下へ
    context.lineTo(0, height); //パスをCanvasの左下へ
    context.closePath() //パスを閉じる
    context.fill(); //
    context_b.lineTo(width_b + 10, height_b); //パスをCanvasの右下へ
    context_b.lineTo(0, height_b); //パスをCanvasの左下へ
    context_b.closePath() //パスを閉じる
    context_b.fill(); //塗りつぶす
    context_c.lineTo(width_c + 10, height_c); //パスをCanvasの右下へ
    context_c.lineTo(0, height_c); //パスをCanvasの左下へ
    context_c.closePath() //パスを閉じる
    context_c.fill(); //塗りつぶす
    context_d.lineTo(width_d + 10, height_d); //パスをCanvasの右下へ
    context_d.lineTo(0, height_d); //パスをCanvasの左下へ
    context_d.closePath() //パスを閉じる
    context_d.fill(); //塗りつぶす
    context_e.lineTo(width_e + 10, height_e); //パスをCanvasの右下へ
    context_e.lineTo(0, height_e); //パスをCanvasの左下へ
    context_e.closePath() //パスを閉じる
    context_e.fill(); //塗りつぶす
    context_f.lineTo(width_f + 10, height_f); //パスをCanvasの右下へ
    context_f.lineTo(0, height_f); //パスをCanvasの左下へ
    context_f.closePath() //パスを閉じる
    context_f.fill(); //塗りつぶす
    context_g.lineTo(width_g + 10, height_g); //パスをCanvasの右下へ
    context_g.lineTo(0, height_g); //パスをCanvasの左下へ
    context_g.closePath() //パスを閉じる
    context_g.fill(); //塗りつぶす
}

/**
 * Function to draw sine
 * 
 * The sine curve is drawn in 10px segments starting at the origin. 
 * drawSine(時間, 波の幅のzoom, 波の開始位置の遅れ)
 */
function drawSine(t, zoom, delay) {

    // Set the initial x and y, starting at 0,0 and translating to the origin on
    // the canvas.
    var x = t; //時間を横の位置とする
    var y = Math.sin(x)/zoom;
    context.moveTo(yAxis, unit*y+xAxis); //スタート位置にパスを置く
    context_b.moveTo(yAxis_b, unit*y+xAxis_b);
    context_c.moveTo(yAxis_c, unit*y+xAxis_c);
    context_d.moveTo(yAxis_d, unit*y+xAxis_d);
    context_e.moveTo(yAxis_e, unit*y+xAxis_e);
    context_f.moveTo(yAxis_f, unit*y+xAxis_f);
    context_g.moveTo(yAxis_g, unit*y+xAxis_g);
    
    // Loop to draw segments (横幅の分、波を描画)
    for (i = yAxis; i <= width + 10; i += 10) {
        x = t+(-yAxis+i)/unit/zoom;
        y = Math.sin(x - delay)/9;
        context.lineTo(i, unit*y+xAxis);
        context_b.lineTo(i, unit*y+xAxis_b);
        context_c.lineTo(i, unit*y+xAxis_c);
        context_d.lineTo(i, unit*y+xAxis_d);
        context_e.lineTo(i, unit*y+xAxis_e);
        context_f.lineTo(i, unit*y+xAxis_f);
        context_g.lineTo(i, unit*y+xAxis_g);
    }
}

init();
    
});;

