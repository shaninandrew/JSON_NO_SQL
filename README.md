# Сервер хранения Json объектов (Python/C#) // JSON_NO_SQL

Две программы демонстраторы: сервер, написанный на Python, умеющий принимать на хранение и выдавать JSON объекты по их ID (простой Redis-подобный), со встроенным кэшем 
для ускорения его работы. Понимает Content-length и Chunk запросы.

Клиентская часть: простая C# программа, создающая объект-пример персоны, с документами и контактами, которая загружает на данный NoSQL сервер данные для хранения (каталог Json файлов с доступом по Id (из самого JSona)).

