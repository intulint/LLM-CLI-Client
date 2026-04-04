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
MAX_TOOL_CALLS = 5
current_tool_calls = 0

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


def tool_message(tool_call_object):
    # tool_call_object — это элемент из массива assistant_tool_calls
    call_id = tool_call_object["id"]
    name = tool_call_object["function"]["name"]

    try:
        args = json.loads(tool_call_object["function"]["arguments"])
    except json.JSONDecodeError as e:
        # Отправляем валидный tool-ответ с ошибкой парсинга
        error_response = {
            "role": "tool",
            "tool_call_id": call_id,
            "content": f"ERROR: Failed to parse arguments: {e}"
        }
        chat_form.append(error_response)
        generate_api_request(None)
        return  # Выходим, не выполняем логику

    print("\n=== Tool use ===")
    print(f"Tool name: {name}")
    print(f"Arguments: {args}")

    
    # Выполняем логику
    result = ""
    if name == "fetch":
        result = fetch_tool(args.get('url', ''))
    else:
        result = f"ERROR: Unknown tool {name}"

    tool_response = {
            "role": "tool",
            "tool_call_id": call_id,
            "content": result
        }
    
    global current_tool_calls
    current_tool_calls+=1
    if current_tool_calls == 1:
        tool_response["content"] += f"\n[Notice: You are allowed a maximum of {MAX_TOOL_CALLS} consecutive tool calls in total, across all tools for this request. Plan your usage efficiently and provide a final answer when the limit is reached.]"
    elif current_tool_calls == MAX_TOOL_CALLS - 1:
        tool_response["content"] += "\n[Notice: One more tool call allowed. Make it count and then provide a final answer.]"
    elif current_tool_calls > MAX_TOOL_CALLS:
        tool_response["content"] = "ERROR: Tool execution limit reached. Do not use any more tools. Provide a final answer to the user based on available information."

    chat_form.append(tool_response)
    generate_api_request(None)


# Функция для запроса списка моделей на сервере
def model_api_request():
    # Отправляем GET-запрос на сервер
    response = requests.get(server_url + "/v1/models")
    # Выводим ID первой модели, которая вернулась от сервера
    print("Модель: " + response.json()["data"][0]["id"])


# Функция для генерации ответа на запрос пользователя
def generate_api_request(message_input):
    """
    Генерирует запрос к API. Поддерживает режим стриминга и обычный запрос.
    Обработка reasoning_content и tool_calls сохранена.
    """
    # Добавляем в форму чата сообщение
    if message_input is not None:
        chat_form.append(message_input)
        # print(message_input)
        
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
        current_tool_calls = []
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
                                print("\n=========Thinking=========\n")  # Исправлено: корректный заголовок

                            chunks += content
                            print(content, end="")

                        # 3. Обработка вызовов инструментов (tool_calls)
                        if delta.get("tool_calls"):
                            for tc_delta in delta.get("tool_calls"):
                            # 1. Если пришел ID, значит это начало нового вызова в массиве
                                if "id" in tc_delta:
                                    current_tool_calls.append({
                                        "id": tc_delta["id"],
                                        "name": "",
                                        "arguments": ""
                                    })
    
                                # 2. Дописываем аргументы и имя к последнему вызову в списке
                                if current_tool_calls:
                                    last_call = current_tool_calls[-1]
                                    if "function" in tc_delta:
                                        f = tc_delta["function"]
                                        if "name" in f: last_call["name"] = f["name"]
                                        if "arguments" in f: last_call["arguments"] += f["arguments"]

                    except json.JSONDecodeError as e:
                        print(f"Ошибка при парсинге JSON чанка: {e}, данные: {data}")
                    except Exception as e:
                        print(f"Ошибка при обработке чанка: {e}, строка: {line_str}")

            except Exception as e:
                print(f"Ошибка декодирования строки: {e}")

        if current_tool_calls:
            # Формируем массив tool_calls для истории
            assistant_tool_calls = []
            for tc in current_tool_calls:
                assistant_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                })
            
            # Добавляем в историю именно так!
            chat_form.append({"role": "assistant","tool_calls": assistant_tool_calls})
    
            # Теперь запускаем выполнение инструментов
            for tc in assistant_tool_calls:
                tool_message(tc) # Передаем весь объект вызова
        else:
            # Если вызовов не было, добавляем обычный текст
            chat_form.append({"role": "assistant", "content": chunks.strip()})


    # --- ЛОГИКА ОБЫЧНОГО ЗАПРОСА ---
    else:
        try:
            message = response.json()["choices"][0].get("message", {})

            # 1. Обработка reasoning_content в обычном режиме
            if Print_thinking and message.get("reasoning_content"):
                text = message.get("reasoning_content").strip()
                print("=========Thinking=========")
                print(text)
                print("=========Thinking=========\n")

            # 2. Обработка tool_calls 
            if message.get("tool_calls"):
                # Сохраняем вызов в историю
                chat_form.append(message)
                # Запускаем каждый вызов
                for tc in message["tool_calls"]:
                    # Превращаем структуру в удобный для tool_message вид
                    tool_call_obj = {
                        "id": tc["id"],
                        "function": tc["function"]
                    }
                    tool_message(tool_call_obj)
            # 3. Вывод контента
            elif message.get("content"):
                content = message["content"].strip()
                print(f"Assistant: {content}")
                chat_form.append({"role": "assistant", "content": content})

        except Exception as e:
            print(f"Ошибка при обработке нестриминг ответа: {e}")

# Функция для печати сообщений чата
def message_print(messages):
    print("Содержание чата:")
    # Проходимся по каждому сообщению в чате и выводим его на экран
    for message in messages:
        print(message.get("role") + ": ", end='')
        if message.get("content"):
            print(message.get("content"))
        if message.get("tool_calls"):
            print(message.get("tool_calls"))

# Основная функция программы
def main():
    # Вызываем функцию для запроса списка моделей
    model_api_request()
    # Выводим сообщение об команде окончании работы программы
    comands = """
            Команды:
            Справка                         > /h
            Выход                           > /q 
            Удаление сообщения              > /d
            Регенерация сообщения           > /r
            Новый чат                       > /n
            Стриминг переключение           > /s
            Отображение мыслей переключение > /t
            Вывести текущий контекст        > /p """
    print(comands)
    print()
    # Печатаем начальные сообщения чата
    message_print(chat_form)
    # Запускаем бесконечный цикл для обработки запросов пользователя
    while True:
        # Запрашиваем ввод пользователя
        user_input = input("\n> ").strip()

        if not user_input:
            continue  # Пропустить пустой ввод

        # Если пользователь ввел 'q', завершаем программу
        if user_input == "/q":
            print("Выход.")
            break
        
        if user_input == "/h":
            print(comands)
            continue

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
        global current_tool_calls
        current_tool_calls = 0
        generate_api_request({"role": "user", "content": user_input})


# Если модуль запущен как основной, вызываем функцию main()
if __name__ == "__main__":
    main()
