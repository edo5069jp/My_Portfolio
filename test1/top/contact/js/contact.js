document.addEventListener("DOMContentLoaded", function(){
  const form = document.getElementById("form");
  const button = document.getElementById("button");

  form.addEventListener("input", update);
  form.addEventListener("change", update);

  function update() {
    //入力内容確認ボタンの有効・無効切り替え
    const isRequired = form.checkValidity();
    if (isRequired) {
      button.disabled = false;
      button.style.cursor = "pointer";
      button.classList.add("active");
    } else {
      button.disabled = true;
      button.style.cursor = "auto";
      button.classList.remove("active");
    }

    //電話番号の処理
    document.getElementById("tel").addEventListener("change", function(e){
      var data = e.target.value;
      var hankaku = data.replace(/[Ａ-Ｚａ-ｚ０-９]|\－|\＋/g,function(s){return String.fromCharCode(s.charCodeAt(0) - 0xFEE0)});

      //半角数字と+-のみ残す
      var zenkakuDel = new String(hankaku).match(/\d|\-|\+/g);
      if(zenkakuDel !== null){
        zenkakuDel = zenkakuDel.join("");
      }
      this.value = zenkakuDel;
    });

    //メールアドレスの処理
    document.getElementById("email").addEventListener("input", function(){
      var zenkigou = "＠－ー＋＿．，、";
      var hankigou = "@--+_...";
      var data = this.value;
      var str = "";

      //指定された全角記号のみを半角に変換
      for (i = 0; i < data.length; i++)
      {
          var dataChar = data.charAt(i);
          var dataNum = zenkigou.indexOf(dataChar,0);
          if (dataNum >= 0) dataChar = hankigou.charAt(dataNum);
          str += dataChar;
      }

      //アルファベットと数字の変換処理
      var hankaku = str.replace(/[Ａ-Ｚａ-ｚ０-９]/g,function(s){return String.fromCharCode(s.charCodeAt(0)-0xFEE0)});
      this.value = hankaku;
    });
  };

});