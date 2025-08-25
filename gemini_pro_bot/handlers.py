import asyncio
from gemini_pro_bot.llm import (
    get_model, 
    get_model_list_text, 
    AVAILABLE_MODELS, 
    DEFAULT_MODEL,
    get_model_name_by_id
)
from google.generativeai.types.generation_types import (
    StopCandidateException,
    BlockedPromptException,
)
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from telegram.error import NetworkError, BadRequest
from telegram.constants import ChatAction, ParseMode
from gemini_pro_bot.html_format import format_message
import PIL.Image as load_image
from io import BytesIO


def new_chat(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the selected model for this chat, or use default
    selected_model = context.chat_data.get("selected_model", DEFAULT_MODEL)
    model = get_model(selected_model)
    context.chat_data["chat"] = model.start_chat()


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\nStart sending messages with me to generate a response.\n\nSend /new to start a new chat session.\nSend /model to see available models.",
        # reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Basic commands:
/start - Start the bot
/help - Get help. Shows this message

Chat commands:
/new - Start a new chat session (model will forget previously generated messages)
/model - Show available models and current selection

Model Selection:
Send a number (1-4) to select a model:
1 - Gemini 2.5 Pro
2 - Gemini 2.5 Flash  
3 - Gemini 2.5 Flash Lite
4 - Gemini 2.5 Flash Live

Send a message to the bot to generate a response.
Gemini Pro Wrapper by HPD47
"""
    await update.message.reply_text(help_text)


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new chat session."""
    init_msg = await update.message.reply_text(
        text="Starting new chat session...",
        reply_to_message_id=update.message.message_id,
    )
    new_chat(context)
    selected_model = context.chat_data.get("selected_model", DEFAULT_MODEL)
    model_name = get_model_name_by_id(selected_model)
    await init_msg.edit_text(f"New chat session started with {model_name}.")


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available models and current selection."""
    selected_model = context.chat_data.get("selected_model", DEFAULT_MODEL)
    current_model_name = get_model_name_by_id(selected_model)
    
    model_list = get_model_list_text()
    message = f"*Current Model:* {current_model_name}\n\n{model_list}"
    
    await update.message.reply_text(
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=update.message.message_id,
    )


async def handle_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle model selection when user sends a number 1-5."""
    text = update.message.text.strip()
    
    if text in AVAILABLE_MODELS:
        # Valid model selection
        model_info = AVAILABLE_MODELS[text]
        old_model = context.chat_data.get("selected_model", DEFAULT_MODEL)
        context.chat_data["selected_model"] = model_info["id"]
        
        # Start a new chat with the selected model
        new_chat(context)
        
        await update.message.reply_text(
            text=f"✅ Model changed to *{model_info['name']}*\n\n{model_info['description']}\n\nNew chat session started automatically.",
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=update.message.message_id,
        )
        return True
    
    return False


# Define the function that will handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages from users.

    First checks if the message is a model selection (1-5).
    If not, checks if a chat session exists for the user, initializes a new session if not.
    Sends the user's message to the chat session to generate a response.
    Streams the response back to the user, handling any errors.
    """
    # Check if this is a model selection
    if await handle_model_selection(update, context):
        return
    
    if context.chat_data.get("chat") is None:
        new_chat(context)
    text = update.message.text
    init_msg = await update.message.reply_text(
        text="Generating...", reply_to_message_id=update.message.message_id
    )
    await update.message.chat.send_action(ChatAction.TYPING)
    # Generate a response using the text-generation pipeline
    chat = context.chat_data.get("chat")  # Get the chat session for this chat
    response = None
    try:
        # Use synchronous API in a thread; omit stream kw if unsupported
        response = await asyncio.to_thread(chat.send_message, text)
    except StopIteration:
        await init_msg.edit_text(
            "Selected model returned no output (possibly unavailable). Choose another model with /model."
        )
        return
    except StopCandidateException as sce:
        print("Prompt: ", text, " was stopped. User: ", update.message.from_user)
        print(sce)
        await init_msg.edit_text("The model unexpectedly stopped generating.")
        chat.rewind()  # Rewind the chat session to prevent the bot from getting stuck
        return
    except BlockedPromptException as bpe:
        print("Prompt: ", text, " was blocked. User: ", update.message.from_user)
        print(bpe)
        await init_msg.edit_text("Blocked due to safety concerns.")
        if response:
            # Resolve the response to prevent the chat session from getting stuck
            await response.resolve()
        return
    full_plain_message = ""
    try:
        # Non-streaming handling with robust safety / empty candidate diagnostics
        if not response:
            await init_msg.edit_text("No response object returned from model.")
            return

        candidate = None
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                for part in candidate.content.parts:
                    txt = getattr(part, "text", None)
                    if txt:
                        full_plain_message += txt

        # If still empty, attempt legacy text accessor carefully
        if not full_plain_message:
            fallback_text = getattr(response, "text", None)
            if fallback_text:
                full_plain_message = fallback_text

        if full_plain_message:
            message = format_message(full_plain_message)
            await init_msg.edit_text(
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return

        # Diagnose why empty
        reasons = []
        if candidate:
            # Safety ratings
            safety_ratings = getattr(candidate, "safety_ratings", []) or []
            blocked_categories = []
            for r in safety_ratings:
                prob = getattr(r, "probability", None)
                cat = getattr(r, "category", None)
                prob_name = getattr(prob, "name", None)
                cat_name = getattr(cat, "name", None)
                if prob_name in ("MEDIUM", "HIGH"):
                    blocked_categories.append(cat_name or "UNKNOWN")
            if blocked_categories:
                reasons.append("Safety filter triggered: " + ", ".join(blocked_categories))
            finish_reason = getattr(candidate, "finish_reason", None)
            finish_name = getattr(finish_reason, "name", None)
            if finish_name:
                reasons.append(f"Finish reason: {finish_name}")
        else:
            reasons.append("No candidates returned (model may be unavailable or ID invalid)")

        diagnostic = "; ".join(reasons) if reasons else "Unknown reason"
        await init_msg.edit_text(
            f"Model produced no text. {diagnostic}. Try another model (/model) or rephrase."
        )
    except Exception as e:
        print("Post-processing error:", e)
        await init_msg.edit_text("Error processing model response.")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming images with captions and generate a response."""
    init_msg = await update.message.reply_text(
        text="Generating...", reply_to_message_id=update.message.message_id
    )
    
    # Get the selected model for this chat
    selected_model = context.chat_data.get("selected_model", DEFAULT_MODEL)
    img_model = get_model(selected_model)
    
    images = update.message.photo
    unique_images: dict = {}
    for img in images:
        file_id = img.file_id[:-7]
        if file_id not in unique_images:
            unique_images[file_id] = img
        elif img.file_size > unique_images[file_id].file_size:
            unique_images[file_id] = img
    file_list = list(unique_images.values())
    file = await file_list[0].get_file()
    a_img = load_image.open(BytesIO(await file.download_as_bytearray()))
    prompt = None
    if update.message.caption:
        prompt = update.message.caption
    else:
        prompt = "Analyse this image and generate response"
    try:
        response = await asyncio.to_thread(img_model.generate_content, [prompt, a_img])
    except StopIteration:
        await init_msg.edit_text(
            "Image request produced no output (model unavailable). Try another model with /model."
        )
        return
    except Exception as e:
        print("Image generation call failed:", e)
        await init_msg.edit_text("Error calling image model.")
        return

    full_plain_message = ""
    try:
        candidate = None
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                for part in candidate.content.parts:
                    txt = getattr(part, "text", None)
                    if txt:
                        full_plain_message += txt
        if not full_plain_message:
            fallback_text = getattr(response, "text", None)
            if fallback_text:
                full_plain_message = fallback_text
        if full_plain_message:
            message = format_message(full_plain_message)
            await init_msg.edit_text(
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return
        # Diagnose
        reasons = []
        if candidate:
            safety_ratings = getattr(candidate, "safety_ratings", []) or []
            blocked_categories = []
            for r in safety_ratings:
                prob = getattr(r, "probability", None)
                cat = getattr(r, "category", None)
                prob_name = getattr(prob, "name", None)
                cat_name = getattr(cat, "name", None)
                if prob_name in ("MEDIUM", "HIGH"):
                    blocked_categories.append(cat_name or "UNKNOWN")
            if blocked_categories:
                reasons.append("Safety filter triggered: " + ", ".join(blocked_categories))
            finish_reason = getattr(candidate, "finish_reason", None)
            finish_name = getattr(finish_reason, "name", None)
            if finish_name:
                reasons.append(f"Finish reason: {finish_name}")
        else:
            reasons.append("No candidates returned (model may be unavailable or ID invalid)")
        diagnostic = "; ".join(reasons) if reasons else "Unknown reason"
        await init_msg.edit_text(
            f"Image model produced no text. {diagnostic}. Try another model or image."
        )
    except Exception as e:
        print("Image post-processing error:", e)
        await init_msg.edit_text("Error processing image response.")
