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


def fetch_tool(url):
    # Функция для получения содержимого по URL
    try:
        # Отправляем GET-запрос с таймаутом 30 секунд
        resp = requests.get(url, timeout=30)
        # Вызываем исключение, если статус ответа не 2xx
        resp.raise_for_status()
        content = resp.text
        return content
    except Exception:
        # Возвращаем сообщение об ошибке при неудаче
        return "Failed to read the response."


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

Stream = True  # Потоковая генерация токенов
Thinking = None  # режим размышлений
Print_thinking = True  # отображать размышления

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


# Функция для запроса списка моделей на сервере
def model_api_request():
    # Отправляем GET-запрос на сервер
    response = requests.get(server_url + "/models")
    # Выводим ID первой модели, которая вернулась от сервера
    print("Модель: " + response.json()["data"][0]["id"])


# Функция для генерации ответа на запрос пользователя
def generate_api_request():
    """
    Генерирует запрос к API. Поддерживает режим стриминга и обычный запрос.
    Обработка reasoning_content и tool_calls сохранена.
    """

    # --- ЛОГИКА СТРИМИНГА ---
    if Stream:
        try:
            response = requests.post(
                server_url + "/chat/completions",
                headers=headers,
                json=chat_request,
                stream=Stream,
                timeout=120,  # Добавлен таймаут для безопасности
            )
            response.raise_for_status()  # Проверка на ошибки HTTP
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при создании запроса: {e}")
            return

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

                        # 1. Обработка размышлений (reasoning_content)
                        if Print_thinking and delta.get("reasoning_content"):
                            reasoning = delta.get("reasoning_content")
                            if not is_reasoning:
                                is_reasoning = True
                                print(f"=========Thinking=========")
                            print(reasoning, end="")

                        # 2. Обработка основного ответа (content)
                        if delta.get("content"):
                            content = delta.get("content")
                            # Логика переключения: если было мышление, теперь конец мышления
                            if is_reasoning and not is_content:
                                is_content = True
                                print(
                                    f"=========End of Reasoning========="
                                )  # Исправлено: корректный заголовок

                            chunks += content
                            print(content, end="")

                        # 3. Обработка вызовов инструментов (tool_calls)
                        if delta.get("tool_calls"):
                            is_tool = True
                            tool_def = delta["tool_calls"][0]["function"]
                            if tool_def.get("name"):
                                tool_name = tool_def["name"]
                            if tool_def.get("arguments"):
                                tool_arguments += tool_def["arguments"]

                    except json.JSONDecodeError as e:
                        print(f"Ошибка при парсинге JSON чанка: {e}, данные: {data}")
                    except Exception as e:
                        print(f"Ошибка при обработке чанка: {e}, строка: {line_str}")

            except Exception as e:
                print(f"Ошибка декодирования строки: {e}")

        # Обработка итогов
        if is_tool:
            is_tool = False
            tool_requests = {
                "function": {"name": tool_name, "arguments": tool_arguments}
            }
            print(tool_requests["function"])
            if callable(tool_message):
                tool_message(tool_requests)
            else:
                print(f"Функция tool_message не найдена или не вызываема")

        print()  # Перенос строки после завершения
        # Сохраняем только контент в чат-формат
        chat_form.append({"role": "assistant", "content": chunks})

    # --- ЛОГИКА ОБЫЧНОГО ЗАПРОСА ---
    else:
        try:
            response = requests.post(
                server_url + "/v1/chat/completions", headers=headers, json=chat_request
            )
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]

            # 1. Обработка reasoning_content в обычном режиме
            if Print_thinking and message.get("reasoning_content"):
                reasoning = message["reasoning_content"]
                print(f"=========Thinking=========")
                print(reasoning)
                print(f"=========End of Reasoning=========\n")

            # 2. Обработка tool_calls
            if "tool_calls" in message and message["tool_calls"]:
                print(message["tool_calls"][0]["function"])
                if callable(tool_message):
                    tool_message(message["tool_calls"][0])
                else:
                    print("Ошибка: tool_message не является вызываемым объектом")

            # 3. Вывод контента
            if message.get("content"):
                print(message["role"] + ": " + message["content"])

            chat_form.append(message)

        except Exception as e:
            print(f"Ошибка при обработке нестриминг ответа: {e}")

def tool_message(tool_result):
    # {'function': {'name': 'fetch', 'arguments': '{'}}
    print("\n=== Tool use ===")
    print("Tool name:", tool_result["function"]["name"])
    print("Arguments:", tool_result["function"]["arguments"])

    tool_name = tool_result["function"]["name"]
    # Парсим аргументы как JSON
    tool_arguments = json.loads(tool_result["function"]["arguments"])

    # Создаем ответ для инструмента
    tool_response = {"role": "tool", "content": ""}
    if tool_name == "fetch":
        url = tool_arguments.get("url")
        # Вызываем функцию fetch_tool с полученным URL
        tool_response["content"] = fetch_tool(url)

    # print(tool_response ["role"] + ": " + tool_response ["content"])
    # Добавляем результат инструмента в историю
    chat_form.append(tool_response)
    generate_api_request()


# Функция для печати сообщений чата
def message_print(messages):
    # Проходимся по каждому сообщению в чате и выводим его на экран
    for message in messages:
        print(message["role"] + ": " + message["content"])


# Основная функция программы
def main():
    # Вызываем функцию для запроса списка моделей
    model_api_request()
    # Выводим сообщение об команде окончании работы программы
    print("""
            Команды:
            Выход       = /q 
            Удаление    = /d
            Регенерация = /r
            Новый чат   = /n""")
    print()
    # Печатаем начальные сообщения чата
    message_print(chat_form)
    # Запускаем бесконечный цикл для обработки запросов пользователя
    while True:
        # Запрашиваем ввод пользователя
        user_input = input("> ")
        # Если пользователь ввел 'q', завершаем программу
        if user_input == "/q":
            print("Выход.")
            break

        if user_input == "/d":
            if len(chat_form) > 2:
                chat_form.pop()
                chat_form.pop()
                print("Удалено")
                message_print(chat_form)
            else:
                print("Удалять нечего")
            continue

        if user_input == "/n":
            print("Новая сессия.")
            chat_form.clear()
            chat_form.append({"role": "system", "content": system_prompt})
            chat_form.append({"role": "assistant", "content": first_message})
            message_print(chat_form)
            continue

        if user_input == "/r":
            chat_form.pop()
            print("Регенерация сообщения.")
            user_input = chat_form.pop()["content"]

        # Добавляем в форму чата сообщение пользователя
        chat_form.append({"role": "user", "content": user_input})

        # Генерируем ответ на запрос пользователя
        generate_api_request()


# Если модуль запущен как основной, вызываем функцию main()
if __name__ == "__main__":
    main()