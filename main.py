# This code has been accelerated by ChatGPT, Microsoft Copilot, and Github Copilot.
import discord
import json
import os
import asyncio
import random
from difflib import get_close_matches
from discord.ext import commands
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

def get_function(name):
    if name == 'load':
        def load_memory(file_path: str) -> dict:
            """
            Load memory from a JSON file.

            Args:
                file_path (str): Path to the JSON file.

            Returns:
                dict: Loaded memory data.
            """
            with open(file_path, "r") as file:
                memory: dict = json.load(file)
            return memory
        return load_memory
    elif name == 'save':
        def save_memory(file_path: str, memory: dict) -> None:
            """
            Save memory to a JSON file.

            Args:
                file_path (str): Path to the JSON file.
                memory (dict): Memory data to be saved.

            Returns:
                None
            """
            with open(file_path, 'w') as file:
                json.dump(memory, file, indent=2)
        return save_memory
    elif name == 'match':
        def find_match(user_question: str, questions: list[str]) -> str:
            """
            Find a matching question from a list of questions.

            Args:
                user_question (str): User's question.
                questions (list[str]): List of questions to search from.

            Returns:
                str: Matched question.
            """
            matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.6)
            return matches[0] if matches else None
        return find_match
    elif name == 'collect':
        def collect_answer(question: str, responses_base: dict) -> str:
            """
            Collect an answer for a given question from memory.

            Args:
                question (str): Question to find answer for.
                responses_base (dict): Dictionary containing questions and answers.

            Returns:
                str: Answer for the question.
            """
            for q in responses_base["questions"]:
                if q['question'] == question:
                    return q["answer"]
            return None  # Return None if no answer is found
        return collect_answer
    else:
        print("Error, check function parameters.")

# Initialize the Discord bot with command support
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)


@bot.event
async def on_ready() -> None:
    """
    Event triggered when the bot is ready.
    """
    print(f"We have logged in as {bot.user}")

@bot.command(name='commands')
async def bot_commands(ctx):
    """
    Provide help for all the available commands.

    Args:
        ctx (discord.ext.commands.Context): Context object representing the context of the command.

    Returns:
        None
    """
    help_message = """
    Here are the available commands:
    - `b!teach`: teach blubbert new things to say
    - `b!qb`: the handy dandy quotebook

    Use `b![command] help` to get more information about a specific command.
    """
    await ctx.send(help_message)

@bot.group(invoke_without_command=True, name='teach')
async def teach(ctx, *, trigger) -> None:
    """
    Teach the bot a new response using the b!teach command.

    Args:
        ctx (discord.ext.commands.Context): Context object representing the context of the command.

    Returns:
        None
    """

    await ctx.send(f"What would you like me to say in response to '{trigger}'?\n\ntype 'cancel' to cancel.")

    def check_message(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for('message', timeout=60, check=check_message)
        if message.content.lower() == 'cancel':
            await ctx.send("Kk.")
            return
        
        responses = get_function("load")("responses.json")
        
        # Find a similar trigger in the responses
        similar_trigger = next((response for response in responses if fuzz.ratio(response['trigger'], trigger) > 70), None)

        # If a similar trigger is found, append the new response to its list
        if similar_trigger is not None:
            similar_trigger['responses'].append(message.content)
        # If no similar trigger is found, create a new trigger-response pair
        else:
            responses.append({'trigger': trigger, 'responses': [message.content]})
        
        get_function("save")('responses.json', responses)
        await ctx.send("Thanks for teaching me!")

    except TimeoutError:
        await ctx.send("Sorry I got bored, start from the beginning plz.")

@teach.command(name='help')
async def teach_help(ctx) -> None:
    """
    Provide help for the teach command.

    Args:
        ctx (discord.ext.commands.Context): Context object representing the context of the command.

    Returns:
        None
    """
    help_message = """
    The `teach` command allows you to teach the bot a new response.
    
    Usage: `b!teach`
    
    Follow the prompts to provide a question and an answer for the bot.
    
    Example:
    ```
    User: b!teach How are you?
    Bot: What would you like me to say in response to 'How are you?'?
    User: I'm doing great!
    Bot: Thanks for teaching me!
    ```
    """
    await ctx.send(help_message)

@bot.group(invoke_without_command=True, name='qb') # Quotebook
async def qb(ctx, author_name=None) -> None:
   
    data = get_function("load")("quotes.json")

    if data['authors']:
        if author_name:
            # Find the author in the data
            author = next((author for author in data['authors'] if author['name'].lower() == author_name.lower()), None)
            if not author:
                await ctx.send(f"No quotes available for {author_name}.")
                return
        else:
            # If no author is specified, select a random author
            author = random.choice(data['authors'])

        quote = random.choice(author['quotes'])
        await ctx.send(f"\"{quote}\" - {author['name'].capitalize()}")
    else:
        await ctx.send("No quotes available.")

@qb.command(name='add')
async def qb_add(ctx, author_name, *, quote):
    data = get_function("load")("quotes.json")

    # Find the author in the data
    author = next((author for author in data['authors'] if author['name'].lower() == author_name.lower()), None)

    if author:
        # If the author exists, add the quote to their list of quotes
        author['quotes'].append(quote)
    else:
        # If the author does not exist, create a new author with the quote
        data['authors'].append({'name': author_name, 'quotes': [quote]})

    # Write the updated data back to the file
    get_function("save")("quotes.json", data)

    await ctx.send(f"Added quote to {author_name}.")

@qb.command(name='help')
async def qb_help(ctx) -> None:
    """
    Provide help for the qb command.

    Args:
        ctx (discord.ext.commands.Context): Context object representing the context of the command.

    Returns:
        None
    """
    help_message = """
    The `qb` command allows you to get a random quote from the quotebook or add a new quote.
    
    Usage: `b!qb [author_name]`
    
    If an `author_name` is provided, a random quote from that author will be displayed. If no `author_name` is provided, a random quote from any author will be displayed.
    
    Example:
    ```
    User: b!qb
    Bot: "To be or not to be, that is the question." - William Shakespeare
    User: b!qb Shakespeare
    Bot: "All the world's a stage, and all the men and women merely players." - William Shakespeare
    ```
    
    To add a new quote, use the `add` subcommand:
    
    Usage: `b!qb add [author_name] [quote]`
    
    Example:
    ```
    User: b!qb add Einstein E=mc^2
    Bot: Added quote to Einstein.
    ```
    """
    await ctx.send(help_message)

@bot.event
async def on_message(message) -> None:
    """
    Event triggered when a message is received.

    Args:
        message (discord.Message): Message object representing the received message.

    Returns:
        None
    """
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

    if "blubbert" in message.content.lower() and "b!" not in message.content.lower():
        load_memory = get_function("load")
        find_match = get_function("match")

        responses = load_memory("responses.json")
        match = find_match(message.content.lower(), [q['trigger'] for q in responses])
        if match:
            collect_answer = get_function("collect")
            await message.channel.send(collect_answer(match,responses))


        else:
            trigger = message.content
            await message.channel.send("Heckin Uhhh, I don't really know what you are talking about. Would you like to show me what to say to that? (Yes/No)")
            try:
                response = await bot.wait_for('message', timeout=30, check=lambda m: m.author == message.author and m.channel == message.channel)
                if response.content.lower() == 'yes':

                    save_memory = get_function("save")
                    
                    await message.channel.send("Got it! What's the quirky thing I say or do?")
                    answer = await bot.wait_for('message', timeout=30, check=lambda m: m.author == message.author and m.channel == message.channel)
                    responses.append({'trigger': trigger, 'responses': answer.content})
                    save_memory('responses.json', responses)
                    await message.channel.send("Thanks for teaching me!")
                else:
                    await message.channel.send("Alright, let me know if you change your mind!")
            except asyncio.TimeoutError:
                await message.channel.send("Sorry I got bored, start from the beginning plz.")


# Run the bot
bot.run(TOKEN)
