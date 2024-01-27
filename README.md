# Парсер Списка Перечня Олимпиад (РСШОР) на Python

- Супер простой (или *элегантный*) код
- Ноль зависимостей (`html.parser` + `http.client`)
- Ясная абстракция (олимпиада это олимпиада, легче чем читать оригинальную таблицу, где НТО это 20+ пунктов!)
- Просто пример как надо делать такие парсеры без всяких `BeautfulSoup`
- Легкое решение ваших проблем

# Как использовать?

Всё логично и просто, есть три вещи, которые вы можете захотеть импортнуть

1. Класс олимпиады (`Olymp`).  Поля
    - `number: int` - номер олимпиады в списке
    - `name: str` - название
    - `url: str` - ссылка на их сайт
    - `lesson: str` - предмет олимпиады
    - `level: int` - уровень олимпиады (1-3)

    Ксати хочу заметить, что тут олимпиады с одним название, но с разными предметами - разные олимпиады, хоть и они буду схожи всем кроме `lesson` и `level`, получается что в результате парсинга будет 27 Высших Проб и 2 Гранита Науки

2. `Parser`.  Просто класс парсера, наследуемый от `html.parser.HTMLParser`.  Вам наверное будут интересны методы `feed` - добавить html и `parsed_olymps` - вернуть распаршенные олимпиады

3. `parse_from_web`.  Просто разпарсить олимпиады по URL, ожидается что страница будет хотя бы похожа на https://rsr-olymp.ru