import random
import asyncio
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== RAILWAY ENVIRONMENT VARIABLES ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN_ID = int(os.getenv("OWNER_ID", "0"))

# Files to store data
ADMINS_FILE = "authorized_admins.json"
ALLOWED_GROUPS_FILE = "allowed_groups.json"

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump(list(admins), f)

def load_allowed_groups():
    if os.path.exists(ALLOWED_GROUPS_FILE):
        with open(ALLOWED_GROUPS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_allowed_groups(groups):
    with open(ALLOWED_GROUPS_FILE, 'w') as f:
        json.dump(list(groups), f)

AUTHORIZED_ADMINS = load_admins()
ALLOWED_GROUPS = load_allowed_groups()

# Cheat settings
cheat_mode = {"coin": "random", "dice": "random"}
next_forced = {"coin": None, "dice": None}

# ========== Authorization Check ==========
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is authorized (EITHER in list OR group admin)"""
    user_id = update.effective_user.id
    
    if user_id == SUPER_ADMIN_ID:
        return True
    
    if user_id in AUTHORIZED_ADMINS:
        return True
    
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            chat_member = await context.bot.get_chat_member(
                update.effective_chat.id, 
                user_id
            )
            if chat_member.status in ["administrator", "creator"]:
                return True
        except:
            pass
    
    return False

async def is_group_allowed(update: Update):
    """Check if group is allowed to use bot"""
    chat_id = update.effective_chat.id
    return chat_id in ALLOWED_GROUPS

# ========== Owner Only Command ==========
async def agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner types 'agree' in group to allow bot usage there"""
    # Check if user is super admin
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Only bot owner can use this command!")
        return
    
    # Check if in group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ This command only works in groups!")
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    
    if chat_id in ALLOWED_GROUPS:
        await update.message.reply_text(f"✅ Group '{chat_title}' is already allowed to use this bot!")
    else:
        ALLOWED_GROUPS.add(chat_id)
        save_allowed_groups(ALLOWED_GROUPS)
        await update.message.reply_text(
            f"✅ **BRAMHA ESCROW APPROVED!**\n\n"
            f"Group '{chat_title}' is now allowed to use this bot.\n"
            f"Admins can now use /coin and /dice commands."
        )

# ========== Super Admin DM Commands ==========
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new admin - Super Admin only"""
    if update.effective_chat.type != "private":
        return
    
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Only super admin can use this!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Usage:** `/addadmin <user_id>`\n\n"
            "Example: `/addadmin 123456789`"
        )
        return
    
    try:
        new_id = int(context.args[0])
        
        if new_id == SUPER_ADMIN_ID:
            await update.message.reply_text("❌ This is the super admin already!")
            return
        
        AUTHORIZED_ADMINS.add(new_id)
        save_admins(AUTHORIZED_ADMINS)
        await update.message.reply_text(f"✅ **Admin added!**\nUser ID: `{new_id}`")
        
        try:
            await context.bot.send_message(
                new_id, 
                "🎉 **You've been granted admin access!**\n\n"
                "Use `/admin` in DM to control game outcomes.\n"
                "Use `/coin` and `/dice` in allowed groups."
            )
        except:
            pass
    except:
        await update.message.reply_text("❌ Invalid user ID!")

async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove admin - Super Admin only"""
    if update.effective_chat.type != "private":
        return
    
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Only super admin can use this!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/removeadmin <user_id>`")
        return
    
    try:
        rm_id = int(context.args[0])
        
        if rm_id == SUPER_ADMIN_ID:
            await update.message.reply_text("❌ Cannot remove super admin!")
            return
        
        if rm_id in AUTHORIZED_ADMINS:
            AUTHORIZED_ADMINS.discard(rm_id)
            save_admins(AUTHORIZED_ADMINS)
            await update.message.reply_text(f"✅ Admin `{rm_id}` removed!")
            
            try:
                await context.bot.send_message(rm_id, "⚠️ Your admin access has been revoked.")
            except:
                pass
        else:
            await update.message.reply_text(f"❌ User not found.")
    except:
        await update.message.reply_text("❌ Invalid ID!")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all admins - Super Admin only"""
    if update.effective_chat.type != "private":
        return
    
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Only super admin can use this!")
        return
    
    if not AUTHORIZED_ADMINS:
        await update.message.reply_text("📋 No authorized admins yet.")
    else:
        admin_list = "\n".join([f"• `{admin_id}`" for admin_id in AUTHORIZED_ADMINS])
        await update.message.reply_text(
            f"📋 **Authorized Admins:**\n\n{admin_list}\n\n"
            f"**Total:** {len(AUTHORIZED_ADMINS)}"
        )

async def listgroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all allowed groups - Super Admin only"""
    if update.effective_chat.type != "private":
        return
    
    if update.effective_user.id != SUPER_ADMIN_ID:
        await update.message.reply_text("❌ Only super admin can use this!")
        return
    
    if not ALLOWED_GROUPS:
        await update.message.reply_text("📋 No groups allowed yet. Use /agree in a group to allow it.")
    else:
        group_list = "\n".join([f"• Group ID: `{gid}`" for gid in ALLOWED_GROUPS])
        await update.message.reply_text(
            f"📋 **Allowed Groups:**\n\n{group_list}\n\n"
            f"**Total:** {len(ALLOWED_GROUPS)} groups"
        )

# ========== Game Logic (2-3 Seconds) ==========
def get_result(game_type):
    """Get result with hidden cheat system"""
    if next_forced[game_type] is not None:
        forced = next_forced[game_type]
        next_forced[game_type] = None
        return forced
    
    mode = cheat_mode[game_type]
    if game_type == "coin":
        if mode == "head":
            return "Head"
        if mode == "tail":
            return "Tail"
        return random.choice(["Head", "Tail"])
    else:
        if mode != "random":
            return mode
        return random.randint(1, 6)

async def show_animation(update: Update, context: ContextTypes.DEFAULT_TYPE, game_type: str):
    """Show animation for 2-3 seconds total"""
    if game_type == "coin":
        msg = await update.message.reply_text("🪙 Flipping coin.")
    else:
        msg = await update.message.reply_text("🎲 Rolling dice.")
    
    # Animation frames with 1 second each (total 2 seconds)
    for i in range(2):
        await asyncio.sleep(1)
        if game_type == "coin":
            await msg.edit_text(f"🪙 Flipping coin{'..' * (i+1)}")
        else:
            await msg.edit_text(f"🎲 Rolling dice{'..' * (i+1)}")
    
    await asyncio.sleep(0.5)
    return msg

# ========== Group Commands (Check Group Permission First) ==========
async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flip a coin - shows result in 2-3 seconds"""
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ This bot only works in groups!")
        return
    
    # Check if group is allowed
    if not await is_group_allowed(update):
        await update.message.reply_text(
            "❌ **BRAMHA ESCROW - Group Not Authorized!**\n\n"
            "This group is not allowed to use this bot.\n"
            "Contact @clerkMM to get access."
        )
        return
    
    if not await is_authorized(update, context):
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You need to EITHER:\n"
            "1️⃣ Be added as an authorized admin, OR\n"
            "2️⃣ Be an admin of this group"
        )
        return
    
    anim_msg = await show_animation(update, context, "coin")
    result = get_result("coin")
    emoji = "🪙" if result == "Head" else "💰"
    await anim_msg.edit_text(f"{emoji} **{result}**! {emoji}")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll a dice - shows result in 2-3 seconds"""
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ This bot only works in groups!")
        return
    
    # Check if group is allowed
    if not await is_group_allowed(update):
        await update.message.reply_text(
            "❌ **BRAMHA ESCROW - Group Not Authorized!**\n\n"
            "This group is not allowed to use this bot.\n"
            "Contact @clerkMM to get access."
        )
        return
    
    if not await is_authorized(update, context):
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You need to EITHER:\n"
            "1️⃣ Be added as an authorized admin, OR\n"
            "2️⃣ Be an admin of this group"
        )
        return
    
    anim_msg = await show_animation(update, context, "dice")
    result = get_result("dice")
    dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    await anim_msg.edit_text(f"🎲 **{result}** {dice_emojis[result-1]}")

# ========== Admin Panel (DM ONLY) ==========
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Secret admin panel - ONLY works in DM"""
    
    if update.effective_chat.type in ["group", "supergroup"]:
        return
    
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    is_auth = False
    
    if user_id == SUPER_ADMIN_ID:
        is_auth = True
    elif user_id in AUTHORIZED_ADMINS:
        is_auth = True
    
    if not is_auth:
        await update.message.reply_text("❌ You are not authorized!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🪙 Coin Control", callback_data="menu_coin")],
        [InlineKeyboardButton("🎲 Dice Control", callback_data="menu_dice")],
        [InlineKeyboardButton("⚡ Force Next Roll", callback_data="menu_next")],
        [InlineKeyboardButton("📊 Current Settings", callback_data="status")]
    ]
    await update.message.reply_text(
        "🔧 **Admin Control Panel**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel buttons"""
    query = update.callback_query
    await query.answer()
    
    if query.message.chat.type != "private":
        await query.edit_message_text("❌ This panel only works in DM!")
        return
    
    user_id = query.from_user.id
    is_auth = False
    
    if user_id == SUPER_ADMIN_ID:
        is_auth = True
    elif user_id in AUTHORIZED_ADMINS:
        is_auth = True
    
    if not is_auth:
        await query.edit_message_text("❌ Access denied!")
        return
    
    data = query.data
    
    if data == "menu_coin":
        keyboard = [
            [InlineKeyboardButton("🪙 Force HEAD", callback_data="cheat_coin_head")],
            [InlineKeyboardButton("💰 Force TAIL", callback_data="cheat_coin_tail")],
            [InlineKeyboardButton("🎲 Random", callback_data="cheat_coin_random")],
            [InlineKeyboardButton("◀️ Back", callback_data="back")]
        ]
        current = cheat_mode["coin"]
        await query.edit_message_text(
            f"🪙 **Coin Control**\nCurrent: `{current}`",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "menu_dice":
        keyboard = [
            [InlineKeyboardButton("⚀ Force 1", callback_data="cheat_dice_1")],
            [InlineKeyboardButton("⚁ Force 2", callback_data="cheat_dice_2")],
            [InlineKeyboardButton("⚂ Force 3", callback_data="cheat_dice_3")],
            [InlineKeyboardButton("⚃ Force 4", callback_data="cheat_dice_4")],
            [InlineKeyboardButton("⚄ Force 5", callback_data="cheat_dice_5")],
            [InlineKeyboardButton("⚅ Force 6", callback_data="cheat_dice_6")],
            [InlineKeyboardButton("🎲 Random", callback_data="cheat_dice_random")],
            [InlineKeyboardButton("◀️ Back", callback_data="back")]
        ]
        current = cheat_mode["dice"]
        await query.edit_message_text(
            f"🎲 **Dice Control**\nCurrent: `{current}`",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "menu_next":
        keyboard = [
            [InlineKeyboardButton("🪙 Next Coin: HEAD", callback_data="next_coin_head")],
            [InlineKeyboardButton("💰 Next Coin: TAIL", callback_data="next_coin_tail")],
            [InlineKeyboardButton("🎲 Next Dice: 1", callback_data="next_dice_1")],
            [InlineKeyboardButton("🎲 Next Dice: 2", callback_data="next_dice_2")],
            [InlineKeyboardButton("🎲 Next Dice: 3", callback_data="next_dice_3")],
            [InlineKeyboardButton("🎲 Next Dice: 4", callback_data="next_dice_4")],
            [InlineKeyboardButton("🎲 Next Dice: 5", callback_data="next_dice_5")],
            [InlineKeyboardButton("🎲 Next Dice: 6", callback_data="next_dice_6")],
            [InlineKeyboardButton("◀️ Back", callback_data="back")]
        ]
        await query.edit_message_text(
            "⚡ **Force Next Roll** (One time only)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("cheat_coin_"):
        mode = data.split("_")[-1]
        cheat_mode["coin"] = mode
        await query.edit_message_text(f"✅ Coin set to: `{mode}`")
    
    elif data.startswith("cheat_dice_"):
        mode = data.split("_")[-1]
        cheat_mode["dice"] = int(mode) if mode.isdigit() else mode
        await query.edit_message_text(f"✅ Dice set to: `{cheat_mode['dice']}`")
    
    elif data.startswith("next_coin_"):
        result = "Head" if data.endswith("head") else "Tail"
        next_forced["coin"] = result
        await query.edit_message_text(f"✅ Next coin: `{result}` (one time)")
    
    elif data.startswith("next_dice_"):
        num = int(data.split("_")[-1])
        next_forced["dice"] = num
        await query.edit_message_text(f"✅ Next dice: `{num}` (one time)")
    
    elif data == "status":
        status_text = f"""
📊 **Current Settings**

🪙 **Coin**: `{cheat_mode['coin']}`
🎲 **Dice**: `{cheat_mode['dice']}`

⚡ **Next Forced**:
• Coin: `{next_forced['coin'] or 'None'}`
• Dice: `{next_forced['dice'] or 'None'}`

👑 **Authorized Admins**: {len(AUTHORIZED_ADMINS)}
📋 **Allowed Groups**: {len(ALLOWED_GROUPS)}
        """
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="back")]]
        await query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "back":
        keyboard = [
            [InlineKeyboardButton("🪙 Coin Control", callback_data="menu_coin")],
            [InlineKeyboardButton("🎲 Dice Control", callback_data="menu_dice")],
            [InlineKeyboardButton("⚡ Force Next Roll", callback_data="menu_next")],
            [InlineKeyboardButton("📊 Current Settings", callback_data="status")]
        ]
        await query.edit_message_text(
            "🔧 **Admin Control Panel**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ========== Start Command ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if username == "clerkMM" or user_id == SUPER_ADMIN_ID:
        await update.message.reply_text(
            "👑 **BRAMHA ESCROW - Super Admin**\n\n"
            "📝 **DM Commands:**\n"
            "/addadmin <id> - Add user\n"
            "/removeadmin <id> - Remove user\n"
            "/listadmins - List users\n"
            "/listgroups - List allowed groups\n"
            "/admin - Control panel\n\n"
            "🎮 **Group Commands:**\n"
            "/agree - Allow group to use bot (type in group)\n"
            "/coin - Flip coin (2-3 sec)\n"
            "/dice - Roll dice (2-3 sec)\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 **Developer:** @clerkMM\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
    elif user_id in AUTHORIZED_ADMINS:
        await update.message.reply_text(
            "✅ **BRAMHA ESCROW - Authorized**\n\n"
            "/admin - Control panel (DM only)\n"
            "/coin - Flip coin\n"
            "/dice - Roll dice\n\n"
            "⚠️ Bot works only in groups where owner has typed /agree"
        )
    else:
        await update.message.reply_text(
            "❌ **BRAMHA ESCROW - Access Denied**\n\n"
            "You are not authorized to use this bot.\n\n"
            "Contact @clerkMM for access."
        )

# ========== Main ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Owner commands
    app.add_handler(CommandHandler("agree", agree))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("listadmins", listadmins))
    app.add_handler(CommandHandler("listgroups", listgroups))
    
    # Public commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coin", coin))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("=" * 50)
    print("🤖 BRAMHA ESCROW BOT STARTED!")
    print(f"👑 Owner ID: {SUPER_ADMIN_ID}")
    print(f"📋 Authorized users: {len(AUTHORIZED_ADMINS)}")
    print(f"📋 Allowed groups: {len(ALLOWED_GROUPS)}")
    print("=" * 50)
    print("✅ Bot is running on Railway!")
    print("⏱️  Animation: 2-3 seconds")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
