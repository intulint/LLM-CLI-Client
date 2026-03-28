import requests
import json

# Определяем системный промпт, который будет использоваться для модели
system_prompt = "I am an assistant, ready to help the user."

# Первое сообщение, которое отправляет ассистент
first_message = "Hello, how can I help?"

# Форма чата, которая содержит системный промпт и первое сообщение ассистента
chat_form = [
    {"role": "system", "content": system_prompt},
    {"role": "assistant", "content": first_message},
]

# URL сервера, на который будут отправляться запросы
server_url = "http://localhost:8080"

# Заголовки для HTTP-запросов, включая токен авторизации (в данном случае - 'no-key')
headers = {"Content-Type": "application/json", "Authorization": "Bearer no-key"}

Stream = True  # Потоковая генерация токенов
Print_thinking = True  # отображать размышления

tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch",
            "description": "download a url into context",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "url to fecth"}
                },
                "required": ["url"],
            },
        },
    }
]

# Запрос на генерацию чата, который включает модель, форму чата и температуру
chat_request = {
    "max_tokens": 4000,
    "messages": chat_form,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "stream": Stream,
    "tools": tools,
    "tool_choice": "auto",
}


def fetch_tool(url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        # Возвращаем четкую структуру ошибки
        return f"ERROR: {type(e).__name__}: {str(e)}" 


def tool_message(tool_result):
    # {'name': 'fetch', 'arguments': '{'}
    print("\n=== Tool use ===")
    print("Tool name:", tool_result.get("name"))
    print("Arguments:", tool_result.get("arguments"))

    tool_name = tool_result["name"]
    # Парсим аргументы как JSON
    tool_arguments = json.loads(tool_result.get("arguments"))

    # Создаем ответ для инструмента
    tool_response = {"role": "tool", "content": ""}
    if tool_name == "fetch":
        url = tool_arguments.get("url")
        # Вызываем функцию fetch_tool с полученным URL
        tool_response["content"] = fetch_tool(url).strip()

    generate_api_request(tool_response)


# Функция для запроса списка моделей на сервере
def model_api_request():
    # Отправляем GET-запрос на сервер
    response = requests.get(server_url + "/models")
    # Выводим ID первой модели, которая вернулась от сервера
    print("Модель: " + response.json()["data"][0]["id"])


# Функция для генерации ответа на запрос пользователя
def generate_api_request(message_input):
    """
    Генерирует запрос к API. Поддерживает режим стриминга и обычный запрос.
    Обработка reasoning_content и tool_calls сохранена.
    """
    # Добавляем в форму чата сообщение
    chat_form.append(message_input)
    print(message_input)
    # --- ЛОГИКА СТРИМИНГА ---
    
    try:
        response = requests.post(
            server_url + "/v1/chat/completions",
            headers=headers,
            json=chat_request,
            stream=Stream
        )
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при создании запроса: {e}")
        return
    
    if Stream:

        chunks = ""
        tool_name = ""
        tool_arguments = ""
        is_tool = False
        is_reasoning = False
        is_content = False

        for line in response.iter_lines():
            if not line:
                continue
            try:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]  # Убираем префикс "data: "
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        # print(delta)
                        # 1. Обработка размышлений (reasoning_content)
                        if Print_thinking and delta.get("reasoning_content"):
                            reasoning = delta.get("reasoning_content")
                            if not is_reasoning:
                                is_reasoning = True
                                print("=========Thinking=========")
                            print(reasoning, end="")

                        # 2. Обработка основного ответа (content)
                        if delta.get("content"):
                            content = delta.get("content")
                            # Логика переключения: если было мышление, теперь конец мышления
                            if is_reasoning and not is_content:
                                is_content = True
                                print("=========Thinking=========\n")  # Исправлено: корректный заголовок

                            chunks += content
                            print(content, end="")

                        # 3. Обработка вызовов инструментов (tool_calls)
                        if delta.get("tool_calls"):
                            # print(delta.get("tool_calls"))
                            is_tool = True
                            tool_def = delta["tool_calls"][0].get("function")
                            if tool_def.get("name"):
                                tool_name = tool_def.get("name")
                            if tool_def.get("arguments"):
                                tool_arguments += tool_def.get("arguments")

                    except json.JSONDecodeError as e:
                        print(f"Ошибка при парсинге JSON чанка: {e}, данные: {data}")
                    except Exception as e:
                        print(f"Ошибка при обработке чанка: {e}, строка: {line_str}")

            except Exception as e:
                print(f"Ошибка декодирования строки: {e}")

        # Обработка итогов
        if is_tool:
            is_tool = False
            tool_requests = {"function": {"name": tool_name, "arguments": tool_arguments}}
            # print(tool_requests["function"])
            if callable(tool_message):
                tool_message(tool_requests.get("function"))
            else:
                print(f"Функция tool_message не найдена или не вызываема")

        print()  # Перенос строки после завершения
        
        # Сохраняем только контент в чат-формат
        chat_form.append({"role": "assistant", "content": chunks.strip()})

    # --- ЛОГИКА ОБЫЧНОГО ЗАПРОСА ---
    else:
        try:
            message = response.json()["choices"][0].get("message")

            # 1. Обработка reasoning_content в обычном режиме
            if Print_thinking and message.get("reasoning_content"):
                text = message.get("reasoning_content").strip()
                print("=========Thinking=========")
                print(text)
                print("=========Thinking=========\n")

            # 2. Вывод контента
            if message.get("content"):
                text = message.get("content").strip()
                print(message["role"] + ": " + text)
                chat_form.append({"role": "assistant", "content": text}) 

            # 3. Обработка tool_calls
            if message.get("tool_calls"):
                text = message["tool_calls"][0].get("function")
                print(text)
                if callable(tool_message):
                    tool_message(text)
                else:
                    print("Ошибка: tool_message не является вызываемым объектом")

        except Exception as e:
            print(f"Ошибка при обработке нестриминг ответа: {e}")

# Функция для печати сообщений чата
def message_print(messages):
    print("Содержание чата:")
    # Проходимся по каждому сообщению в чате и выводим его на экран
    for message in messages:
        print(message.get("role") + ": " + message.get("content"))

# Основная функция программы
def main():
    # Вызываем функцию для запроса списка моделей
    model_api_request()
    # Выводим сообщение об команде окончании работы программы
    print("""
            Команды:
            Выход                           > /q 
            Удаление сообщения              > /d
            Регенерация сообщения           > /r
            Новый чат                       > /n
            Стриминг переключение           > /s
            Отображение мыслей переключение > /t
            Вывести текущий контекст        > /p """)
    print()
    # Печатаем начальные сообщения чата
    message_print(chat_form)
    # Запускаем бесконечный цикл для обработки запросов пользователя
    while True:
        # Запрашиваем ввод пользователя
        user_input = input("> ").strip()

        # Если пользователь ввел 'q', завершаем программу
        if user_input == "/q":
            print("Выход.")
            break
        
        if user_input == "/p":
            message_print(chat_form)
            continue

        if user_input == "/s":
            global Stream
            if Stream:
                Stream = False
                chat_request["stream"] = Stream
                print("stream off")
            else:
                Stream = True
                chat_request["stream"] = Stream
                print("stream on")
            continue

        if user_input == "/t":
            global Print_thinking
            if Print_thinking:
                Print_thinking = False
                print("print thinking off")
            else:
                Print_thinking = True
                print("print thinking on")
            continue

        if user_input == "/d":
            found_user = False
            # Ищем с конца, находим последний элемент с role == "user"
            for i in reversed(range(len(chat_form))):
                if chat_form[i].get("role") == "user":
                    del chat_form[i:]
                    found_user = True
                    break
            
            if found_user:
                print("Последнее сообщение удалено")
                message_print(chat_form)
            else:
                print("Удалять нечего")
            continue

        if user_input == "/n":
            found_user = False
            # Ищем с начала, находим первый элемент с role == "user"
            for i in range(len(chat_form)):
                if chat_form[i].get("role") == "user":
                    del chat_form[i:]
                    found_user = True
                    break   
            if found_user:
                print("Новая сессия.")
                message_print(chat_form)
            else:
                print("Новая сессия уже начата.")
            continue

        if user_input == "/r":
            found_user = False
            for i in reversed(range(len(chat_form))):
                if chat_form[i].get("role") == "user":
                    same_text = chat_form[i].get("content")
                    del chat_form[i:]
                    found_user = True
                    break
            if found_user:
                print("Регенерация сообщения.")
                generate_api_request({"role": "user", "content": same_text})
                continue
            else:
                print("Нечего регенерировать, это новая сессия.")
                continue 

        # Генерируем ответ на запрос пользователя
        generate_api_request({"role": "user", "content": user_input})


# Если модуль запущен как основной, вызываем функцию main()
if __name__ == "__main__":
    main()
