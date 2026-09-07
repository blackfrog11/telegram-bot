from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus

TOKEN = "8773388817:AAFGyjYTEoCEor3FCu_KOVWN9TUjHH9yX5o"   # ← 这里填你的Token
new_users = set()

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        if not user.is_bot:
            new_users.add(user.id)
            print(f"新人进群：{user.full_name}")

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in new_users:
        return

    new_users.discard(user.id)

    if update.message.photo:
        # 删除照片
        try:
            await update.message.delete()
        except:
            pass

        # 永久禁言
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
        except Exception as e:
            print(f"禁言失败: {e}")
            return

        # 创建“解除禁言”按钮
        keyboard = [[InlineKeyboardButton("解除禁言", callback_data=f"unmute_{user.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 发送提示（带@用户名 + 按钮）
        mention = user.mention_html()
        text = f"{mention} 由于防止广告进群就发照片会直接永久禁言，误封请联系管理员/@ccabalxhbot"

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        print(f"已禁言：{user.full_name}")

async def unmute_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 只有管理员才能点
    member = await context.bot.get_chat_member(query.message.chat.id, query.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await query.answer("只有管理员才能解除禁言", show_alert=True)
        return

    # 从按钮数据里取出用户ID
    user_id = int(query.data.split("_")[1])

    # 解除禁言（恢复所有权限）
    try:
        await context.bot.restrict_chat_member(
            chat_id=query.message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        await query.edit_message_text(
            text=query.message.text + "\n\n✅ 管理员已解除禁言",
            parse_mode="HTML"
        )
    except Exception as e:
        await query.answer(f"解除失败: {e}", show_alert=True)

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
app.add_handler(MessageHandler(filters.ChatType.GROUPS, check_message))
app.add_handler(CallbackQueryHandler(unmute_button, pattern="^unmute_"))

print("机器人已启动")
app.run_polling()