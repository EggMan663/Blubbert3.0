# This code has been accelerated by ChatGPT
import discord
import json
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from difflib import get_close_matches

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")




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


# Initialize the Discord bot with command support
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready() -> None:
    """
    Event triggered when the bot is ready.
    """
    print(f"We have logged in as {bot.user}")


@bot.command(name='teach')
async def teach_response(ctx) -> None:
    """
    Teach the bot a new response using the !teach command.

    Args:
        ctx (discord.ext.commands.Context): Context object representing the context of the command.

    Returns:
        None
    """
    await ctx.send("What trick would you like to teach me (Type 'cancel' to cancel)")

    def check_message(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for('message', timeout=60, check=check_message)
        if message.content.lower() == 'cancel':
            await ctx.send("Teaching canceled.")
            return

        question = message.content
        await ctx.send(f"Got it! What fun quirky thing should I say to '{question}'?")
        answer = await bot.wait_for('message', timeout=60, check=check_message)
        if answer.content.lower() == 'cancel':
            await ctx.send("Teaching canceled.")
            return

        responses = load_memory("responses.json")
        responses['questions'].append({'question': question, 'answer': answer.content})
        save_memory('responses.json', responses)
        await ctx.send("Thanks for teaching me!")
    except TimeoutError:
        await ctx.send("Teaching timed out. Please try again.")


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

    if "blubbert".lower() in message.content.lower():
        responses = load_memory("responses.json")
        match = find_match(message.content.lower(), [q['question'].lower() for q in responses['questions']])
        if match:
            answer = collect_answer(match, responses)
            if answer:
                await message.channel.send(answer)
            else:
                await message.channel.send("I don't have an answer for that question yet.")

        else:
            await message.channel.send("Heckin Uhhh, I'm not sure about that. Would you like to teach me a new trick? (Yes/No)")
            try:
                response = await bot.wait_for('message', timeout=30, check=lambda m: m.author == message.author and m.channel == message.channel)
                if response.content.lower() == 'yes':
                    await message.channel.send("Sure! What do you want to teach me?")
                    question = await bot.wait_for('message', timeout=30, check=lambda m: m.author == message.author and m.channel == message.channel)
                    await message.channel.send("Got it! What's the quirky thing I say or do?")
                    answer = await bot.wait_for('message', timeout=30, check=lambda m: m.author == message.author and m.channel == message.channel)
                    responses['questions'].append({'question': question.content, 'answer': answer.content})
                    save_memory('responses.json', responses)
                    await message.channel.send("Thanks for teaching me!")
                else:
                    await message.channel.send("Alright, let me know if you change your mind!")
            except asyncio.TimeoutError:
                await message.channel.send("Teaching request timed out.")


# Run the bot
bot.run(TOKEN)
