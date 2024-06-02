import asyncio
from http.server import BaseHTTPRequestHandler
import json
import logging

from src.configs.logging.logging_config import setup_logging
from src.oai_agent.utils.load_assistant_id import load_assistant_id
from src.oai_agent.utils.create_oai_agent import create_agent
from src.autogen_configuration.autogen_config import GetConfig
from src.tools.read_url import read_url as async_read_url
from src.tools.scroll import scroll as async_scroll
from src.tools.jump_to_search_engine import jump_to_search_engine as async_jump_to_search_engine
from src.tools.go_back import go_back as async_go_back
from src.tools.wait import wait as async_wait
from src.tools.click_element import click_element as async_click_element
from src.tools.input_text import input_text as async_input_text
from src.tools.analyze_content import analyze_content as async_analyze_content
from src.tools.save_to_file import save_to_file as async_save_to_file
from src.oai_agent.utils.prompt import prompt

import autogen
from autogen.agentchat import AssistantAgent
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent

import openai

setup_logging()
logger = logging.getLogger(__name__)

def run_async_function(coro):
    """
    Run an async function in the current event loop.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Running within an existing loop
        return loop.create_task(coro)
    else:
        # No loop running, create a new one
        return loop.run_until_complete(coro)

def sync_read_url(url: str):
    return run_async_function(async_read_url(url))

def sync_scroll(direction: str):
    return run_async_function(async_scroll(direction))

def sync_jump_to_search_engine():
    return run_async_function(async_jump_to_search_engine())

def sync_go_back():
    return run_async_function(async_go_back())

def sync_wait():
    return run_async_function(async_wait())

def sync_click_element(query: str):
    return run_async_function(async_click_element(query))

def sync_input_text(query: str):
    return run_async_function(async_input_text(query))

def sync_analyze_content(query: str):
    return run_async_function(async_analyze_content(query))

def sync_save_to_file(data: str):
    return run_async_function(async_save_to_file(data))

def configure_agent(assistant_type: str) -> GPTAssistantAgent:
    """
    Configure the GPT Assistant Agent with the specified tools and instructions.

    Args:
        None

    Returns:
        GPTAssistantAgent: An instance of the GPTAssistantAgent.
    """
    try:
        logger.info("Configuring GPT Assistant Agent...")
        assistant_id = load_assistant_id(assistant_type)
        llm_config = GetConfig().config_list
        logger.info(llm_config)
        oai_config = {
            "config_list": llm_config["config_list"], "assistant_id": assistant_id}
        gpt_assistant = GPTAssistantAgent(
            name=assistant_type, instructions=AssistantAgent.DEFAULT_SYSTEM_MESSAGE, llm_config=oai_config
        )
        logger.info("GPT Assistant Agent configured.")
        return gpt_assistant
    except openai.NotFoundError:
        logger.warning("Assistant not found. Creating new assistant...")
        create_agent(assistant_type)
        return configure_agent(assistant_type)
    except Exception as e:
        logger.error(f"Unexpected error during agent configuration: {str(e)}")
        raise

async def register_functions(agent):
    """
    Register the functions used by the GPT Assistant Agent.

    Args:
        agent (GPTAssistantAgent): An instance of the GPTAssistantAgent.

    Returns:
        None
    """
    logger.info("Registering functions...")
    function_map = {
        "analyze_content": sync_analyze_content,
        "click_element": sync_click_element,
        "go_back": sync_go_back,
        "input_text": sync_input_text,
        "jump_to_search_engine": sync_jump_to_search_engine,
        "read_url": sync_read_url,
        "scroll": sync_scroll,
        "wait": sync_wait,
        "save_to_file": sync_save_to_file,
    }
    agent.register_function(function_map=function_map)
    logger.info("Functions registered.")

def create_user_proxy():
    """
    Create a User Proxy Agent.

    Args:
        None

    Returns:
        UserProxyAgent: An instance of the UserProxyAgent.
    """
    logger.info("Creating User Proxy Agent...")
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
        code_execution_config={
            "work_dir": "coding",
            "use_docker": False,
        },
    )
    logger.info("User Proxy Agent created.")
    return user_proxy

async def main(prompt=prompt):
    """
    Main function to run the GPT Assistant Agent.

    Args:
        None

    Returns:
        None
    """
    try:
        gpt_assistant = configure_agent("BrowsingAgent")
        await register_functions(gpt_assistant)
        user_proxy = create_user_proxy()
        await user_proxy.initiate_chat(gpt_assistant, message=prompt)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            asyncio.run(main())
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Agent executed successfully'.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'An error occurred: {str(e)}'.encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            prompt = data.get('prompt', '')

            if not prompt:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write('Prompt is required.'.encode('utf-8'))
                return

            asyncio.run(main(prompt))
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Agent executed successfully'.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'An error occurred: {str(e)}'.encode('utf-8'))
