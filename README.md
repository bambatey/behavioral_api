# behavioral_api


plan şu user siteye girdiğinde direkt bir sadece bir adet teste giriş kartıyla karşılaşacak şimdilik ismi spr olarak kalabilir o kartın adı. içeri giridğinde 
   de sadeve şu tip bir soru olacak. bir adet context ve o contexte bağlı bir cümle verilecek. o cümlenin de doğru ya da yanlış olduğu user tarafından          
  seçilecek ve bir sonraki context+cümle sorusuna geçilecek. amaç bu. fakat userların karşısına çıkacak context+cümlelerin belirli bir düzeni var. bu yüzden    
  admin page de tekrardan düzenlenmeli. düzen şu şekilde 24 adet context olacak. bu her contextin bir önce yanlı bir de nesne yanlı versiyonları olcak. nesne   
  yanlı version için 6 özne yanlı versiyon için 6 adet toplam her context için 12 adet cümlemiz olacak. userlar context+cümle yi görüp cümlenin doğru mu yanlış 
   mı olduğuna kara verecekler. amaç bu yonde. fakat olması gereken asıl şey şu her user bu context bazında oluşturudğumuz 12 cümleden sadece 1 tanesi ile      
  karşılaşmalılar. yani user 1 gidip belirlediğimiz 24 contexten her contexten 1 soru olmak üzere toplam 24 soru ile karşı karışıya kalmalılar. user 2 de gidip 
   bu 24 sorunun hiçbirini görmemeli. user 2 için de havuzumuzdan bi 24 daha seçilmeli. user 3 gelince de kulanılan 24+24 den hiçbir soru görmemeli. kısacaı    
  24*12 soru her 12 userda bir resetlenmeli ilk 12 user asla aynı soruları görmemeli. sonraki gelecek 12 user de bu döngü tammalanmış olduğunda tekrarlicas aynı   
  şeyi. bir de sahte sorularımız olacak. user test amacımızı anlamasın diye değerlendiremye sokmacağımız sorular olması lazım bunların sayısı da user başına    
  24*2 adet olmalı. bu sorular da bire bir aynı mantıkta olmalı asıl sorularımızla, context+cümleden oluşmalı. istediğim bu yapıya uygun olacak şekilde apiyi arayüzü ve admin page i tekrar 
   tasarlar ve planımı uygula. cümleler ve contextler adimin page üzerinden düzenlenebilri bir şekilde olmalı yine tabi en önemli kısım o.




   cümlelerin özne yanlı veya nesne yanlı diye bir ayrımı yok. contextlerin var.
     yani aslında aynı context dediğim şey iki version olucak bir özne yanlı iki
     nesne yanlı. bu özne yanlı ve nesne yanlı contextlerin toplam 12 cümlesi olucak
     6 + 6 şekilde. fakat bu 6 + 6 cümle aslına şu şekilde : nesne yanlının da özne
     yanlının da cümleleri aynı olcak yani 6 adet cümle olacak her cümleyi iki kere
     kullanıcaz bir nesne yanlı context için bir de özne yanlı context için. ama
     şöyle bir detay var bir user teste başladığına 1. coontextin nesene yanlı cümlelerindein 4.sünü görürse başka bir contextin kesimlikle özne yanlı versiyonun 4. cümlesini görmeli. bu eşleştirme şart. sonraki karşısına çıkacak context+cümle combinasyonlarında ise asla 4. cümleleri görmemeli geri kalan cümleleri görmeli. 