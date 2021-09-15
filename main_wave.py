import random

from vkwave.api import API
from vkwave.bots import PhotoUploader
from vkwave.bots import SimpleLongPollBot, SimpleBotEvent
from vkwave.bots.core.dispatching import filters
from vkwave.client import AIOHTTPClient

from config import TOKEN, GROUP_ID
from msg_proccess import process

bot = SimpleLongPollBot(tokens=TOKEN, group_id=GROUP_ID)
api = API(clients=AIOHTTPClient(), tokens=TOKEN)

photo_uploader = PhotoUploader(api.get_context())

group_dict = {}

group_answer_chance = {}
group_answer_temp = {}
random_params = False
params = {
    'max_length': 256,
    'no_repeat_ngram_size': 3,
    'do_sample': True,
    'top_k': 150,
    'top_p': 0.9,
    'temperature': 0.75,
    'num_return_sequences': 1,
    'device': 'cpu',
    'is_always_use_length': False,
    'length_generate': '1',
}
def_params = params.copy()


def rand_percent(percent=10):
    return random.randint(0, 100 + 1) < percent


@bot.message_handler(filters.CommandsFilter("clear_history"))
async def clear_history(event: SimpleBotEvent):
    group_id = event.object.object.message.peer_id
    group_dict.get(group_id).clear()
    # dialog_history_array.clear()
    await event.answer(message="History cleared")


@bot.message_handler(filters.CommandsFilter("len_history"))
async def len_history(event: SimpleBotEvent):
    group_id = event.object.object.message.peer_id
    await event.answer(message=f"len history {len(group_dict.get(group_id))}")


def change_title(event, group_name):
    import requests
    url = f"https://api.vk.com/method/groups.edit?group_id={GROUP_ID}&title={group_name + '_bot'}&access_token={TOKEN}&v=5.130"
    payload = {}
    headers = {}
    resp = requests.request("GET", url, headers=headers, data=payload)
    return event.answer(message=group_name)


def text_preprocess(inputs):
    size = 0

    inputs_text = ''
    for size, input_ in enumerate(inputs):
        length_param = '-'
        inputs_text += f"|{input_['speaker']}|{length_param}|{input_['text']}"

        if len(inputs_text) > params.get('max_length') - 5:
            break
    inputs_text += f"|1|{params['length_generate']}|"

    return inputs_text, size


async def send_message(event, group_id, dialog_history_array):
    params.update({'temperature': group_answer_temp.get(group_id)})

    dialog_history,size = text_preprocess(dialog_history_array)
    response = process(dialog_history, params)
    bot_message = response.get('outputs')

    dialog_history_array.append({'speaker': 1, 'text': bot_message})

    group_dict.update({group_id: dialog_history_array[-size:]})
    await event.answer(message=bot_message)


@bot.message_handler()
async def echo(event: SimpleBotEvent, ) -> str:
    print(event)
    user_message = event.object.object.message.text
    group_id = event.object.object.message.peer_id
    # global answer_chance
    print(user_message)
    global answer_chance
    global group_answer_temp
    global params
    if not group_answer_temp.get(group_id):
        group_answer_temp.update({group_id: params.get('temperature')})
    rnd = rand_percent(group_answer_chance.get(group_id, 15))

    if len(str(user_message)) < 3:
        return ''

    if group_dict.get(group_id):
        group_dict.get(group_id).append({'speaker': 0, 'text': user_message.replace('бот,', '').replace('Бот,', '')})
    else:
        group_dict.update({group_id: []})
        group_dict.get(group_id).append({'speaker': 0, 'text': user_message.replace('бот,', '').replace('Бот,', '')})

    dialog_history_array = group_dict.get(group_id)
    # dialog_history_array.append({'speaker': 0, 'text': user_message.replace('бот', '').replace('Бот,', '')})
    reply_message = event.object.object.message.reply_message
    print(dialog_history_array)

    if user_message == 'Бот, назови своё имя':
        dialog_array = [{'speaker': 0, 'text': user_message.replace('бот,', '').replace('Бот,', '')}]
        response = process(text_preprocess(dialog_array), params)
        bot_message = response.get('outputs')[0]
        group_name = bot_message.split(' ')[0]
        await change_title(event, group_name)


    elif rnd or 'бот' in user_message or 'Бот' in user_message:
        await send_message(event, group_id, dialog_history_array)

    elif reply_message and reply_message.from_id == -GROUP_ID:
        await send_message(event, group_id, dialog_history_array)


print('ready')
bot.run_forever()
