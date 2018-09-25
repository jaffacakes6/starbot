import discord
from discord.ext import commands
import config as cfg
import logging
from datetime import datetime

client = commands.Bot(command_prefix='?')
logging.basicConfig(level=logging.INFO)
pins = []


@client.event
async def on_ready():
    client.pin_channel = client.get_channel(cfg.d['pin_channel'])
    await client.change_presence(activity=discord.Activity(
                                          type=3, name="you shitpost"))
    logging.info(f'Bot ready')
    logging.debug(f'Channel registered: {client.pin_channel}')


@client.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == cfg.d['emoji']:
        logging.info(f'Reaction added: {user}, {reaction.message}')
        pin = get_pin(reaction.message.id)

        if cfg.d['self-star'] and user == reaction.message.author:
            await reaction.message.channel.send(cfg.d['self_pin_msg'])
            logging.debug('Self-pin rejected')
            return

        if pin:
            logging.debug(f'Updating existing pin {pin["id"]}...')
            pin['stars'] += 1
            pin['users'].append(user.id)
            e = await build_embed(reaction.message, pin)
            pin_msg = await client.pin_channel.get_message(pin['id'])
            await pin_msg.edit(embed=e)
            logging.debug(f'Updated {pin["id"]}')
        else:
            logging.debug(f'Creating new pin...')
            pin = {'id': 0,
                   'stars': 1, 'users': [user.id],
                   'op': {'user': reaction.message.author.id,
                          'channel': reaction.message.channel.id,
                          'message': reaction.message.id}
                   }

            e = await build_embed(reaction.message, pin)
            pin_msg = await client.pin_channel.send(embed=e)
            pin['id'] = pin_msg.id
            pins.append(pin)
            logging.debug(f'Pin created {pin["id"]}')


@client.event
async def on_reaction_remove(reaction, user):
    if reaction.emoji == cfg.d['emoji']:
        logging.info(f'Reaction removed: {user}, {reaction.message}')
        pin = get_pin(reaction.message.id)

        if cfg.d['self-star'] and user == reaction.message.author:
            logging.debug('Self-unpin rejected')
            return

        logging.debug(f'Updating existing pin {pin["id"]}...')
        pin['stars'] -= 1
        pin['users'].remove(user.id)
        pin_msg = await client.pin_channel.get_message(pin['id'])
        if pin['stars'] == 0:
            print('delete')
            await pin_msg.delete()
            pins.remove(pin)
            logging.debug(f'Pin removed ({pin["stars"]} stars) {pin["id"]}')
        else:
            e = await build_embed(reaction.message, pin)
            await pin_msg.edit(embed=e)
            logging.debug(f'Pin updated ({pin["stars"]} stars) {pin["id"]}')


async def build_embed(msg, pin):
    logging.debug("Building embed")
    date = datetime.today().strftime('%d-%m-%Y')
    plural = 'star' if pin['stars'] == 1 else 'stars'

    e = discord.Embed(description=msg.content, color=0xffac33)
    e.set_author(name=f'{msg.author.name} in #{msg.channel.name}',
                 icon_url=msg.author.avatar_url)
    if msg.attachments:
        e.set_image(url=msg.attachments[0].url)
    e.set_footer(text=f'{cfg.d["emoji"]} {pin["stars"]} {plural} • {msg.id} • {date}')

    return e


def get_pin(id):
    try:
        return [pin for pin in pins if pin['op']['message'] == id][0]
    except IndexError:
        return None


client.run(cfg.d['token'])