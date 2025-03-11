Для запуска проекта необходимо запустить виртуальное окружение :
djangovenv/Scripts/activate
Запускем docker на компьютере после загрузки вписываем в терминале:
docker rm my-redis 
docker ps -a | findstr my-redis
docker ps | findstr redis 
docker ps docker run --name my-redis -p 6379:6379 -d redis:alpine
python run_daphne.py
