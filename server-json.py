import threading
import time
import requests
import json
import http.server
import io
import asyncio

# Встроим кэш-ускоритель, чтобы
# часто используемые данные грузились
# в ОЗУ
# Нюанс в том, что можно асинхронно писать сохраняемые данные, и этим выиграть время работы

class CacheMemory:
    cache = dict()
    error="OK";

    def __init__(self):
        self.cache = dict()

    #ВКЛЮЧЕНИЕ async приводит к ошибкам в работе программы
    def store(self,json_data):
        self.error = "OK";
        #вытаскием ключ из данных
        JS_OBJ = dict()
        if type(json_data)==str:
            JS_OBJ = dict( json.loads(json_data))
        else:
            JS_OBJ = json_data

        id = JS_OBJ.get("id")
        #находим в кэше
        if self.cache == None:
            self.cache=dict
        #отладочный код
        data_to_save=str(  JS_OBJ)
        #сохраняем как строку в кэше
        self.cache[id] = data_to_save

        #Асинхронно гоним данные в файл - это самая медленная функция
        #await self.save_to_file(id)
        asyncio.run( self.save_to_file(id))


    def get_by_key(self,id):
        # вытаскием ключ из данных
        # находим в кэше
        # кэш имеет форму
        # id:JSON_text
        #....
        self.error="OK";

        #print ("cache :: ",self.cache)
        if self.cache == None:
            self.cache=dict

        index=self.cache.get(id)
        VALUE = ""

        if index==None:
            #грузим из файла
            VALUE=self.load_from_file(id)

        else:
            VALUE = index
        #возврат как нормального текста
        return (VALUE)


    def load_from_file(self,id):
        try:
            self.error="OK";
            filename = "data//" + id + ".json";
            file = io.open(filename, mode="rb")
            json_data = file.read().decode("utf-8")
            # пишем в поток
            file.close()

            JS_OBJ = dict(json.loads(json_data))
            id = JS_OBJ.get("id")
            # заполняем
            self.cache[id] = str(JS_OBJ)
            self.error = "OK"
        except Exception as msg:
            self.error = msg


    async def save_to_file(self,id):
        # имя файла
        filename = "data//" + id + ".json";
        try:
            file = io.open(filename, mode="wt")
            data = self.cache.get(id)
            file.write(data)
            file.close()
            # сброс на диск
            self.error = "OK"

        except Exception as msg:
            print("Ошибка: ", msg)
            self.error=msg

    def load_cache_from_file(self):
        pass


class RequestHandlerJSON  (http.server.BaseHTTPRequestHandler):
    #def do_HEAD(self):
    #    self.send_response(200)
    _cache = CacheMemory


    def do_GET(self):
        print (" [GET] Try get data..." + str(self.path) + " " +str(self.client_address) + " -> "+self.requestline)

        #формируем ответ
        prefix = "<html><body>"
        suffix = "</body></html>"
        content = "Server collect data from JSON <br>- POST /store +JSON  <br> - POST /get:id - return JSON.<br> Every JSON MUST HAVE FIELD HASH!!! <br> Path:" +self.path

        # направляем ответ
        all_data = (prefix + content + suffix).encode("utf-8");

        print(" [GET] Send response ...")
        self.send_response(200);
        self.send_header("Content-Type","text/html; charset=utf-8")
        #self.send_header("Charset", "utf-8")
        #application/json; charset=utf-8
        self.send_header("Content-length", str(len(all_data)))
        self.end_headers()
        #self.flush_headers()

        print(" [GET] Write data ...")
        self.wbufsize = 1000
        self.wfile.write(all_data)

        # debug
        # print( all_data)
        #self.wfile.flush()
        #self.wfile.close()

        print("Send " + str(len(all_data))+" bytes")



    def do_POST(self):
        print ("[POST] POST: <" + str(self.path) + "> " +str(self.client_address))
        #значение в этой базе
        VALUE = dict()
        CODE = 200;
        MSG = "OK";
        try:
            #считываем данные из потока прочитав его длину
            len_data =0
            try:
                len_data = int(self.headers['Content-Length'])
            except:
                try:
                    len_data = int(self.headers['content-length'])
                except:
                    len_data =0

            print(f"Длина потока {len_data}")

            if (self.path.startswith('/test')):
                print("Headers: ", self.headers);


                if len_data>0:
                    data = (self.rfile.read(len_data)).decode("utf-8")
                else:
                    # if Transfer-Encoding: chunked
                    data = ""
                    i=0;
                    while self.rfile.closed == False:
                        frag = self.rfile.readline().decode("utf-8")[:-2]
                        print(f"{i}>",frag)
                        i=i+1
                        if frag=="0":
                            break

                        else:
                            if (i%2==0):
                                #клеим нечетные строки
                                data =data + str( frag)

                print("Получено от клиента: ",data)


                CODE = 200;
                MSG = "OK";
                VALUE = "Test Ok";
                self.send_response(CODE, MSG);
                self.send_header("Content-type", "application/text")
                self.send_header("Content-Length", str(len(VALUE)))
                self.send_header("Charset", "utf-8")
                self.end_headers()
                # пишем данные в виде байтов
                self.wfile.write(VALUE.encode("utf-8f"))
                print("*** Отправлено тестовое сообщение...")

            #ветка выдающая данные из хранилища
            if (self.path.startswith('/get:')):
                # разбираем id считывания /get:
                # убиарем опасные символы
                hash_id = self.path[5:].replace("\\", "").replace(".", "").replace("/", "").replace(">", "").replace("<", "").replace("*", "")
                #нужно
                hash_string = str(hash_id)

                #значение из кэша - он сканит, что через него проходит и выгружает
                VALUE=_cache.get_by_key(hash_string)

                MSG=_cache.error
                CODE=200;
                if MSG!="OK":
                    print(f"[!]  GET to POst  {_cache.error}  id ={hash_id}")
                    CODE=500;

                self.send_response(CODE, MSG);
                self.send_header("Content-length", str(len(VALUE)))
                self.send_header("Content-type", "application/json")
                self.send_header("Charset", "utf-8")
                self.end_headers()
                #пишем данные в виде байтов
                self.wfile.write(VALUE.encode("utf-8"))
                print("*** Отправлено ...")
                # сброс на клиенту

            #ветка сохранения JSON данных в файл/кэш
            if (self.path == '/store'):
                print("[POST] Read data...")
                #HTTP сервер и клиенты немного менюят данные поэтому заменим, то что они присылают на нормальные значения
                #считываем и конвертим в строку с заменой управляющих струтктур
                #data=[]
                #while (self.rfile.closed==False):
                #    data=self.rfile.read(-1)
                print (self.headers)
                print (f"Длина потока {len_data}")

                # кусок из теста
                if len_data>0:
                    data = (self.rfile.read(len_data)).decode("utf-8")
                    print(" -> CL>0: Получено от клиента: ", data)
                    #питон любит дополнять \\\\
                    data = data.replace("\\\"", "\"").replace("\\\\", "\\")
                    #уточняем длину
                    len_data=len(data)
                    # удаляем кавычки
                    if (data[0] == data[len_data - 1]):
                        data = data[1:-1]

                    print(" -> Обработано:  ", data)


                else:
                    # if Transfer-Encoding: chunked
                    data = ""
                    i=0;
                    while self.rfile.closed == False:
                        frag = self.rfile.readline().decode("utf-8")[:-2]
                        ## debug print(f"{i}>",frag)
                        i=i+1
                        if frag=="0":
                            break

                        else:
                            if (i%2==0):
                                #клеим нечетные строки
                                data =data + str( frag)



                print("Получено от клиента: ",data)



                #пустые данные игнорим
                len_data = len(data)
                if len_data==0: return ;

                print("[P] Data: <" + data+"> Len:"+str(len(data))+" bytes")

                #строка -> JSON -> cache
                JS_OBJ=json.loads(data)
                _cache.store(JS_OBJ)

                MSG = _cache.error
                CODE = 200;
                if MSG != "OK":
                    print (f"[!]  {_cache.error}")
                    CODE = 500;

                self.send_response(CODE, MSG);
                self.send_header("Content-type",'text/plain');
                self.end_headers()

        except Exception as msg:
            CODE = 500;
            MSG = msg

            print (f"[!] {msg}")
            self.send_response(CODE, MSG);
            self.send_header("Content-type", 'text/plain');
            self.end_headers()

        finally:
            #нужно ли
            #self.finish();
            pass



def start_server(server,port):
    #перезапуски сервера
    restarts=0
    while (restarts<10):
        try:
            config = (server, port)
            server = http.server.ThreadingHTTPServer(config, RequestHandlerJSON)
            server.timeout=0
            server.serve_forever()
        except Exception as data_exc:
            print ("Сервер упал: ",data_exc)
        finally:
            restarts = restarts + 1
            print("Сервер перезапускается шаг ", restarts)


#Глабальная переменная
_thread = threading.Thread()
_cache = CacheMemory()

def main(_server, _port):
        #processor = RequestHandlerJSON()
        print ("Запуск сервера...")
        _thread = threading.Thread(target=start_server, args=[_server,_port])
        _thread.daemon=False
        _thread.start()
        time.sleep(2);
        print ("OK")


def self_test(_server, _port):
    print(" ** Готово!")

    print(" Запуск теста:")

    r = requests.get("http://" + _server + ":" + str(_port) + "/test-get")
    print("Self.check = GET ", r.text)
    print("")

    print("Second test...")

    test = {"key": "value", "package": [{"bar": "Значение"}, {"test": "valuex"}], "id": "tests"}
    test2 = {"key": "ключик", "package": [{"bar": "Значение"}, {"test": "valuex"}], "id": "testX2"}

    hash_id = test.get("id")

    print("Test = ", test)
    print("id = ", hash_id)


    send_pack = (json.dumps(test))
    print("-- Тест на запись данных -- ", hash_id)
    print("1) type of send pack  = ", (type(send_pack)))
    print("   Send pack          = ", (send_pack))

    check_pack = dict(json.loads(send_pack))
    print("2) Check pack  =", (type(check_pack)))
    print("3) id  =", ((check_pack.get("id"))))
    print("4) Send  " + str(len(send_pack)) + " bytes : " + send_pack + "--> server ", _server)
    try:
        r = requests.post("http://" + _server + ":" + str(_port) + "/store", json=send_pack)
        print("Тест прошел POST: "+ r.text)
        r = requests.post("http://" + _server + ":" + str(_port) + "/store", json=json.dumps((test2)))
        print("Тест прошел POST: "+ r.text)
    except Exception as exc:
        print("[!]", exc)

    print("-- Тест на чтение ok -- ", hash_id)
    try:
        r = requests.post("http://" + _server + ":" + str(_port) + "/get:" + hash_id)
        print("САМО ПРОВЕРКА чтение данных =>"+str(r.status_code)+" =>",  r.text )
    except Exception as exc:
        print("[!]", exc)


    hash_id="бред"
    print("-- Тест на отсутствующий элемент -- ", hash_id)
    try:
        r = requests.post("http://" + _server + ":" + str(_port) + "/get:" + hash_id)
        print("Self.check  чтение данных =>"+str(r.status_code)+" =>",  r.text )
    except Exception as exc:
        print("[!]", exc)

    print("Кэш ускоритель")
    print(_cache.cache)

    #замеры времени
    s = time.perf_counter()
    hash_id = "testX2"
    print("-- Тест на чтение  много раз-- ", hash_id)
    N=1000
    for i in range(1,N):
        hash_id="testX2"
        if i% 2==1:
            hash_id="tests"

        print( f"->> {hash_id}")
        try:
            r = requests.post("http://" + _server + ":" + str(_port) + "/get:" + hash_id)
            print(str(i)+f". САМО ПРОВЕРКА чтение данных  ключ {hash_id} => {r.status_code} =>{r.text}")
        except Exception as exc:
            print("[!]", exc)
    elapsed = time.perf_counter() - s
    print(f"Исполнено {N} запросов  {elapsed:0.2f} секунд.")



def idle():
    print(" ** Сервер работает? ", _thread.is_alive(), end="\r")
    while _thread.is_alive():
        print(" ** Сервер работает? ",_thread.is_alive(), end="\r")
        time.sleep(10);

# Run server
server="127.0.0.1"
port=8090

main(server,port)
self_test(server,port)
idle()


