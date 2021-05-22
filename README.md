Сенсор TrueConf Server для PRTG
===============================

https://trueconf.ru/products/server/server-videokonferenciy.html - Информация о продукте  TrueConf Server    
https://developers.trueconf.ru/api/server/ - Документация  

Расширенный сенсор для системы мониторинга [PRTG](https://www.ru.paessler.com/prtg)  


### Каналы:
* Конференции (всего, запущено, остановлено)
* Участники конференций (всего, гостей)
* Пользователи (онлайн, офлайн)
* Ошибки авторизации (Пользователи, панель администратора - за 1 минуту и 5 минут)

![image](https://user-images.githubusercontent.com/1285761/119223067-fe408480-baff-11eb-9488-a9cd69836d6f.png)

### Требования:
- Для работы требуется платная версия TrueConf Server для работы API [Подробнее](https://trueconf.ru/prices.html)
- Установленный пакет Microsoft Visual C++ 

### Для добавления в PRTG:
- Скачайте [последний релиз](https://github.com/sys-admin-su/prtg-sensor-trueconf-server/releases/)
- Разместите trueconf-prtg-sensor.exe из архива в CustomSensors/EXEXML директории, куда установлен Удалённый зонд.
- Создайте сенсор, выберите тип "Расширенный EXE/XML" и выберите trueconf-prtg-sensor.exe
- В параметрах запуска укажите через пробел: <токен> <адрес сервера/%host> <порт> <версия API>
- Все пороговые значения требуется настроить после добавления сенсора и формирования каналов.


### Получение токена
В панели администратора в разделе Веб->Безопасность скопируйте или сгенерируйте новый секретный ключ - это и будет токен.

### Использование:
`trueconf-prtg-sensor.exe <token> <hostname> <port> <api_version>`  
Например:  
`trueconf-prtg-sensor.exe token trueconf.example.com 8080 3.3`
  
### Дополнительная информация
Для сборки `trueconf-prtg-sensor.exe` использовался `pytinstaller v4.1` и `python v3.7`

### Лицензия:
Решение распространяется по [лицензии MIT](https://github.com/sys-admin-su/prtg-sensor-trueconf-server/blob/main/LICENSE)