#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from telegram.ext import Updater, CommandHandler, InlineQueryHandler, Filters, MessageHandler, ChosenInlineResultHandler
from telegram import InlineQueryResultCachedSticker
from uuid import uuid4
import logging
import random
from PickleDict import DataBase

# state of the bot
state_SENDSTICKER, state_SENDWORD = 0, 1
states = None


def start(bot, update):
	global states
	userid = update.message.from_user.id

	# We change the state to "send me a sticker"
	if userid not in states.data:
		states.data[userid] = {
			'state': state_SENDSTICKER,
			'stickers' : [],
			'descr': [],
			'uuid': [],
			'times_used': []
		}
	else:
		states.data[userid]['state'] = state_SENDSTICKER

	# We save the dict
	states.save()

	# Send him/her how-to
	bot.sendMessage(
		update.message.chat_id,
		text='Hola, envíame un sticker para añadirlo a la lista de stickers'
	)


def stickerReceived(bot, update):
	global states
	print(states.data)

	userid = update.message.from_user.id
	sticker = update.message.sticker

	# userid should be in states, and we should be waiting a sticker
	if userid in states.data and states.data[userid]['state'] == state_SENDSTICKER:
		# let's save the sticker
		states.data[userid]['stickers'].append(sticker.file_id)

		# and add it a unique ID
		unique_id = uuid4().int
		while unique_id in states.data[userid]['uuid']:
			unique_id = uuid4().int
		else:
			states.data[userid]['uuid'].append(unique_id)

		# Sticker count
		states.data[userid]['times_used'].append(0)

		# let's change the state
		states.data[userid]['state'] = state_SENDWORD

		# let's tell him/her we want now the description
		bot.sendMessage(
			update.message.chat_id,
			text= "Ara enviam la descripció"
		)

		# We save the dict
		states.save()

		print(sticker.file_id)


def descrReceived(bot, update):
	global states
	userid = update.message.from_user.id

	if (userid in states.data and
			    states.data[userid]['state'] == state_SENDWORD and
			    len(states.data[userid]['stickers']) == len(states.data[userid]['descr'])+1 ):
		# let's change the state
		states.data[userid]['state'] = state_SENDSTICKER

		# let's save description
		states.data[userid]['descr'].append(update.message.text)

		# We save the dict
		states.save()

		print(states.data[userid])


def inlinefeedback(bot, update):
	global states
	userid = update.chosen_inline_result.from_user.id
	sticker_uuid = update.chosen_inline_result.result_id

	userdict = states.data[userid]
	arr = list(zip(userdict['stickers'], userdict['descr'], userdict['uuid']))

	print("sticker_uuid in userdict['uuid'] = ", str(sticker_uuid) in userdict['uuid'])

	for i in range(len(arr)):
		if str(userdict['uuid'][i]) == str(sticker_uuid):
			states.data[userid]['times_used'][i] += 1
			states.save()


def inlinequery(bot, update):
	global states

	userid = update.inline_query.from_user.id
	userdict = states.data[userid]

	# New users
	if userid not in states.data or not states.data[userid]:
		bot.answerInlineQuery(
			inline_query_id=update.inline_query.id,
			results=[],
			switch_pm_text="Añadir stickers"
		)
		return

	# Default sort
	arr = list(zip(userdict['stickers'], userdict['descr'], userdict['uuid'], userdict['times_used']))
	sort_stickers = sorted([(sticker, desc, uuid, 0, times_used) for sticker, desc, uuid, times_used in arr],
	                       key=lambda a: a[4],
	                       reverse=True)

	query = str(update.inline_query.query).lower()
	print("qyery = ", query)

	# Users with stickers
	if update.inline_query.query:

		arr = list(zip(userdict['stickers'], userdict['descr'], userdict['uuid'], userdict['times_used']))

		sort_stickers = sorted(
			[ (sticker, desc, uuid, len( set(query.split()) & set(desc.lower().split()) ), times_used)
			  for sticker, desc, uuid, times_used in arr ],
			key = lambda a: a[3]*1000 + a[4],
			reverse=True
		)

	results = list()

	try:
		for sticker, _, uuid, _, _ in sort_stickers[:20]:
			results.append(
				InlineQueryResultCachedSticker(
					id=uuid,
					sticker_file_id = sticker,

				)
			)

		bot.answerInlineQuery(
			inline_query_id=update.inline_query.id,
			results=results,
			switch_pm_text="Añadir más stickers"
		)
	except Exception as e: print(str(e))


def main():
	# Let's create/restore from disk our dict
	global states
	try:
		states = DataBase('./state.dat')
		states = states.load('./state.dat')
		print("try:", states.data)
	except:
		states = DataBase('./state.dat')

	# Set logging format
	logging.basicConfig(
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		level=logging.INFO)

	# Set bot's token
	f = open('.token')
	token = f.read().strip()
	updater = Updater(token)

	'''# TODO: remove this
	for userid, userdict in states.data.items():
		if True or 'uuid' not in states.data[userid]:
			states.data[userid]['uuid'] = [str(uuid4().int) for _ in range(len(userdict['stickers']))]
			states.save()
		if True or 'times_used' not in states.data[userid]:
			states.data[userid]['times_used'] = [0 for _ in range(len(userdict['stickers']))]
			states.save()
	'''

	# Register commands
	updater.dispatcher.add_handler(CommandHandler('start', start))

	# Register receiver
	updater.dispatcher.add_handler(MessageHandler([Filters.sticker], stickerReceived))
	updater.dispatcher.add_handler(MessageHandler([Filters.text], descrReceived))

	# Register inline
	updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
	updater.dispatcher.add_handler(ChosenInlineResultHandler(inlinefeedback))

	# Start bot
	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
