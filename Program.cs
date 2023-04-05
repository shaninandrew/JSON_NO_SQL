using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Encodings;
using System.Text.Json.Serialization.Metadata;
using System.Security;
using System.Security.Cryptography;
using System.Security.Authentication;
using System.Text;
using System.Buffers.Text;
using System.Net.Http.Json;
using System.Net.Http;

PeopleTrust x = new PeopleTrust("Иванова", "Дарья", "Алексеевич", DateTime.Now);
x.Contacts.Add("kuzya@gmail.com");
x.Contacts.Add("+79697878715");
x.Documents.Add(new PeopleTrust.Document_Item("паспорт", "123902389", "Кукуевский с/с Домской области Тридевятого государства"));
x.Documents.Add(new PeopleTrust.Document_Item("паспорт", "123777444", "Новый город, Домской области Тридевятого государства"));

string data = x.GetJson ();
Console.WriteLine(data);

PeopleTrust copy = JsonSerializer.Deserialize<PeopleTrust>(data);
int data_len = data.Length;


HttpClient client = new HttpClient();
using HttpResponseMessage report = await client.PostAsJsonAsync<PeopleTrust>(
        "http://localhost:8090/store",copy );


Console.WriteLine("Данные отправлены. Результат: ", report.StatusCode);
Console.WriteLine("Данные получены: ", report.Content);



/// <summary>
/// Движок
/// </summary>

class PeopleTrust
  {
    string _hash = "";//внутренний хэш

    /// <summary>
    /// Фамилия
    /// </summary>
    public string Surname
    {
        set;
        get;
    }

    /// <summary>
    /// Уникальный номер
    /// </summary>
    public string Id { set; get; }
    /// <summary>
    /// Имя
    /// </summary>
    public string Name { set; get; }
    /// <summary>
    /// Отчество
    /// </summary>
    public string SecondName { set; get; }
    /// <summary>
    /// Дата рождения
    /// </summary>
    public DateTime Birthdate { set; get; }
    
    /// <summary>
    /// Контакты, просто строки в которых можно написать email, сотовые телефоны, адреса
    /// </summary>
    public List<string> Contacts { set; get; }

/// <summary>
/// Тип для записи паспортов, сертификатов и т.п.
/// </summary>
    public struct Document_Item
    {
        public string type_of_doc { set; get; }
        public string number { set; get; }
        public string issuer { set; get; }
        /// <summary>
        /// Дата начала действия
        /// </summary>
        public DateTime activate { set; get; }
        /// <summary>
        /// Дата окончания действия документа
        /// </summary>
        public DateTime deactivate { set; get; }
        public string Hash { set; get; }
        /// <summary>
        /// Картинка base64
        /// </summary>
        public string picture { set; get; } //картинка

        /// <summary>
        /// Создает новый пункт в списке документов
        /// </summary>
        /// <param name="type_of_doc">Тип документа</param>
        /// <param name="number">Номер документа</param>
        /// <param name="issuer">Выдавшее учреждение</param>
        public Document_Item(string type_of_doc, string number, string issuer)
        { 
            this.type_of_doc = type_of_doc;
            this.number = number;
            this.issuer = issuer;

            //ленивый хэш
            string tmp = type_of_doc + " " + number + " " + issuer;
            byte[] span = System.Text.Encoding.Default.GetBytes(tmp);
            SHA512 sha512 = System.Security.Cryptography.SHA512.Create();
            byte[] out_hash = sha512.ComputeHash(span);
            sha512.Dispose();
            this.Hash = Convert.ToBase64String(out_hash);
        }
    }//Document_item
    

/// <summary>
/// Документы
/// </summary>
/// 
public List<Document_Item> Documents { set; get; }

    /// <summary>
    /// Возвращает хэш от фио + дата рождения
    /// </summary>
    public string Hash
    {
        get
        {
            //ленивый хэш
            if (_hash == "")
            {
                string tmp = Surname + " " + Name + " " + SecondName + " " + Birthdate.ToShortDateString();

                byte[] span = System.Text.Encoding.Default.GetBytes(tmp);
                SHA512 sha512 = System.Security.Cryptography.SHA512.Create();
                byte[] out_hash = sha512.ComputeHash(span);
                sha512.Dispose();
                _hash = (Convert.ToBase64String(out_hash));
            }

            return _hash;
        }//get Hash
    }//get

    /// <summary>
    /// Возвращает JSON из PeopleTrust.
    /// Текст можно передать через сеть и продублировать у себя на машине
    /// </summary>
    /// <returns></returns>
    public string GetJson()
    {
        return (JsonSerializer.Serialize<PeopleTrust>(this));
    }
  

    public PeopleTrust()
    { 
        Id=Guid.NewGuid().ToString();
        Surname = "test";
        Name = "value";
        SecondName = "A";
        _hash = "";
        this.Contacts = new List<string>();
        this.Documents = new List<Document_Item>();
    }

    public string ToString()
    { 
        return (Surname + " " + Name + " " + SecondName+" " + Birthdate.ToShortDateString().ToString()+ "->" + Hash);
    }

    /// <summary>
    /// Создает новый объект класса
    /// </summary>
    /// <param name="A">Фамилия</param>
    /// <param name="B">Имя</param>
    ///<param name="C">Отчество</param>
    /// <param name="d">Дата</param>

    public PeopleTrust(string A, string B, string C, DateTime d)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Surname = A;
        this.Name = B;
        this.SecondName = C;
        this.Birthdate = d;
        string t = this.Hash;
        
        this.Contacts = new List<string>();
        this.Documents = new List<Document_Item>();
    }

} // TrustedPeople
