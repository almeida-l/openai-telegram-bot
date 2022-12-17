import string
import time
import threading
import requests
import openai

openai.api_key = ""

bot_handler = "@mybot"
bot_token = ""
base_url = f"https://api.telegram.org/bot{bot_token}"

def is_this_message_talking_with_me(message : string):
  return not message.startswith(bot_handler)

def get_telegram_updates(offset : int):
  return requests.get(f"{base_url}/getUpdates", json={
      "offset": offset,
      "timeout": 30
    }).json()

def handle_telegram_updates(updates, offset, startup_timestamp):
  for update in updates.get('result', {}):
    if update['update_id'] <= offset:
      continue
    
    offset = update["update_id"]

    if not 'message' in update or not 'text' in update['message']:
      continue
    if update["message"]["date"] < startup_timestamp:
      continue
    if not is_this_message_talking_with_me(update['message']['text']):
      continue
    
    thread = threading.Thread(target=handle_message, args=(update, ))
    thread.start()
  
  return offset

def main():
  startup_timestamp = time.time()
  offset = 0
  
  while True:
    updates = get_telegram_updates(offset)
    offset = handle_telegram_updates(updates, offset, startup_timestamp)
    time.sleep(1)

def sanitize_message(message : string):
  message = message[len(bot_handler):]
  if len(message) == 0:
    return ''
  if not message[-1] in string.punctuation:
    message += '.'
  return message.strip()

def handle_message(update):
  message = sanitize_message(update["message"]["text"])
  if len(message) < 2:
    return
  
  thread_info = "Thread launched:\n" \
    f"  update_id: {update['update_id']}\n" \
    f"  User name: {update['message']['from']['first_name']}\n" \
    f"  message: {message[:100].replace('\n', ' ')}"
  print(thread_info)

  max_tokens = 4097-len(message)
  response_text = "Input muito grande."
  if max_tokens > 0:
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=message,
      max_tokens=4097-len(message),
      n=1,
      stop=None,
      temperature=0.5,
      frequency_penalty=0.7,
      presence_penalty=0.8,
      top_p=1,
    )
    response_text = response["choices"][0]["text"].strip()
  
  requests.post(f"{base_url}/sendMessage", json={
    "chat_id": update["message"]["chat"]["id"],
    "text": response_text,
    "reply_to_message_id": update["message"]["message_id"]
  })
  
  thread_info = "Thread finished:\n" \
    f"  update_id: {update['update_id']}\n" \
    f"  User name: {update['message']['from']['first_name']}\n" \
    f"  response: {response_text[:100].replace('\n', ' ')}"
  print(thread_info)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
