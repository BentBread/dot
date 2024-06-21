import os
import time
import asyncio
from queue import Queue
from threading import Thread
import discord
import query_mng

# Discord bot token
DISCORD_TOKEN = 'MTI1Mzc3MDc2OTU1MzU1NTUwOA.G3UlGB.pi6DaIwS7bUsGa9MIN10W9wkPf1O-7FX2oEQJI'


chat_queue = asyncio.Queue()

# Function to process chat messages
async def process_chat_messages():
    while True:
        message = await chat_queue.get()
        if "Dot" in message.content:
            print(f"Triggering query_mng with query: {message.content}")
            query = "This is a discord chat message: " + message.content
            context = query_mng.process_query(query)
            response = query_mng.chat_with_gpt(query, context)
            if response:
                print(f"Output from query_mng: {response}")
                await message.channel.send(response)

# Discord client
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        # Don't let the bot respond to itself
        if message.author == self.user:
            return

        # Put the message in the queue for processing
        await chat_queue.put(message)

async def main():
    # Initialize the database
    query_mng.initialize_db()

    # Create and start the Discord client
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)

    # Start the chat message processor
    asyncio.create_task(process_chat_messages())

    # Run the Discord client
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())