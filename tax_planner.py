# Nigerian Tax Deadlines Telegram Bot - Python Version
# Based on Nigeria Tax Act 2025

import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# ============= CONFIGURATION =============
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # Get from @BotFather
DATA_FILE = 'users.json'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= TAX DEADLINES DATA =============
TAX_DEADLINES = {
    'individual': {
        'name': '👤 Individual Tax Obligations',
        'description': 'PIT, CGT, Stamp Duties - Progressive rates 0%-25%',
        'obligations': [
            {
                'title': 'Registration (Tax ID/TIN)',
                'taxType': 'PIT',
                'dueDate': 'Before commencing business/employment',
                'recurring': False,
                'penalty': '₦50,000 (1st month) + ₦25,000 for each subsequent month',
                'reminderDays': []
            },
            {
                'title': 'Annual Tax Return Filing',
                'taxType': 'PIT',
                'dueDate': 'By 31 January',
                'recurring': True,
                'month': 1,
                'day': 31,
                'description': 'Self-Assessment/Sole Proprietor for preceding year',
                'penalty': '₦100,000 (1st month) + ₦50,000 for each subsequent month',
                'reminderDays': [30, 14, 7, 3, 1]
            },
            {
                'title': 'PAYE Annual Return',
                'taxType': 'PAYE',
                'dueDate': 'By 31 January',
                'recurring': True,
                'month': 1,
                'day': 31,
                'description': 'If employer - for preceding year',
                'penalty': '₦100,000 (1st month) + ₦50,000 for each subsequent month',
                'reminderDays': [30, 14, 7, 3, 1]
            },
            {
                'title': 'Monthly PAYE Remittance',
                'taxType': 'PAYE',
                'dueDate': 'Within 14 days of deduction',
                'recurring': True,
                'monthlyDay': 14,
                'description': 'If employer',
                'penalty': '10% of tax amount + interest + potential criminal liability',
                'reminderDays': [10, 7, 3, 1]
            },
            {
                'title': 'Capital Gains Tax Filing',
                'taxType': 'CGT',
                'dueDate': 'Upon disposal of taxable assets',
                'recurring': False,
                'description': 'Same rules as PIT apply',
                'penalty': 'Standard late filing/payment penalties apply',
                'reminderDays': []
            }
        ]
    },
    'smallBusiness': {
        'name': '📈 Small Business Tax Obligations',
        'description': 'Turnover ≤ ₦100M AND Assets ≤ ₦250M - Exempt from CIT & VAT on sales',
        'obligations': [
            {
                'title': 'Registration (Tax ID/TIN)',
                'taxType': 'CIT',
                'dueDate': 'Before commencing business operations',
                'recurring': False,
                'penalty': '₦50,000 (1st month) + ₦25,000 for each subsequent month',
                'reminderDays': []
            },
            {
                'title': 'Annual Tax Return Filing',
                'taxType': 'CIT',
                'dueDate': 'Within 6 months after accounting year-end',
                'recurring': True,
                'description': '0% Tax Rate - Still must file',
                'penalty': '₦100,000 (1st month) + ₦50,000 for each subsequent month',
                'reminderDays': [60, 30, 14, 7, 3, 1]
            },
            {
                'title': 'Monthly PAYE Remittance',
                'taxType': 'PAYE',
                'dueDate': 'Within 14 days of deduction',
                'recurring': True,
                'monthlyDay': 14,
                'description': 'If employer',
                'penalty': '10% of tax amount + interest + potential criminal liability',
                'reminderDays': [10, 7, 3, 1]
            },
            {
                'title': 'Monthly WHT Remittance',
                'taxType': 'WHT',
                'dueDate': 'Within 21 days of deduction',
                'recurring': True,
                'monthlyDay': 21,
                'description': 'If making payments subject to WHT',
                'penalty': '40% of amount not deducted; 10% p.a. + interest for non-remittance',
                'reminderDays': [14, 7, 3, 1]
            },
            {
                'title': 'Monthly WHT Return',
                'taxType': 'WHT',
                'dueDate': 'By 21st of following month',
                'recurring': True,
                'monthlyDay': 21,
                'description': 'If making payments subject to WHT',
                'penalty': '40% of amount not deducted; 10% p.a. + interest for non-remittance',
                'reminderDays': [14, 7, 3, 1]
            }
        ]
    },
    'company': {
        'name': '🏢 Company Tax Obligations',
        'description': 'Turnover > ₦100M OR Assets > ₦250M - 30% CIT rate',
        'obligations': [
            {
                'title': 'Registration (Tax ID/TIN)',
                'taxType': 'CIT',
                'dueDate': 'Before commencing business operations',
                'recurring': False,
                'penalty': '₦50,000 (1st month) + ₦25,000 for each subsequent month',
                'reminderDays': []
            },
            {
                'title': 'Annual Tax Return Filing',
                'taxType': 'CIT',
                'dueDate': 'Within 6 months after accounting year-end',
                'recurring': True,
                'description': 'Audited accounts and self-assessment',
                'penalty': '₦100,000 (1st month) + ₦50,000 for each subsequent month',
                'reminderDays': [60, 30, 14, 7, 3, 1]
            },
            {
                'title': 'Tax Payment (Self-Assessment)',
                'taxType': 'CIT',
                'dueDate': '30 days after assessment OR 7 months after year-end',
                'recurring': True,
                'description': 'Payment of assessed CIT',
                'penalty': '10% of unpaid tax amount + interest',
                'reminderDays': [21, 14, 7, 3, 1]
            },
            {
                'title': 'Monthly VAT Return Filing',
                'taxType': 'VAT',
                'dueDate': 'By 21st of following month',
                'recurring': True,
                'monthlyDay': 21,
                'description': 'For transactions in preceding month',
                'penalty': '₦100,000 (1st month) + ₦50,000 for each subsequent month',
                'reminderDays': [14, 7, 3, 1]
            },
            {
                'title': 'Monthly VAT Remittance',
                'taxType': 'VAT',
                'dueDate': 'By 14th of following month',
                'recurring': True,
                'monthlyDay': 14,
                'description': 'Payment of VAT collected',
                'penalty': '10% of tax amount + interest + potential imprisonment',
                'reminderDays': [10, 7, 3, 1]
            },
            {
                'title': 'Monthly PAYE Remittance',
                'taxType': 'PAYE',
                'dueDate': 'Within 14 days of deduction',
                'recurring': True,
                'monthlyDay': 14,
                'description': 'Employee tax remittance',
                'penalty': '10% of tax amount + interest + potential criminal liability',
                'reminderDays': [10, 7, 3, 1]
            },
            {
                'title': 'Monthly WHT Remittance',
                'taxType': 'WHT',
                'dueDate': 'Within 21 days of deduction',
                'recurring': True,
                'monthlyDay': 21,
                'description': 'Withholding tax on payments',
                'penalty': '40% of amount not deducted; 10% p.a. + interest for non-remittance',
                'reminderDays': [14, 7, 3, 1]
            },
            {
                'title': 'Monthly WHT Return',
                'taxType': 'WHT',
                'dueDate': 'By 21st of following month',
                'recurring': True,
                'monthlyDay': 21,
                'description': 'WHT filing for preceding month',
                'penalty': '40% of amount not deducted; 10% p.a. + interest for non-remittance',
                'reminderDays': [14, 7, 3, 1]
            }
        ]
    }
}

# ============= USER DATA MANAGEMENT =============
def load_users():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                logger.info(f"Loaded {len(users)} users")
                return users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
    return []

def save_users(users):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def add_user(chat_id, category):
    users = load_users()
    existing = next((u for u in users if u['chatId'] == chat_id), None)
    
    if existing:
        existing['category'] = category
        existing['lastUpdated'] = datetime.now().isoformat()
    else:
        users.append({
            'chatId': chat_id,
            'category': category,
            'active': True,
            'registeredDate': datetime.now().isoformat(),
            'lastUpdated': datetime.now().isoformat()
        })
    
    save_users(users)

def get_user_category(chat_id):
    users = load_users()
    user = next((u for u in users if u['chatId'] == chat_id), None)
    return user['category'] if user else None

# ============= BOT COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    welcome_message = """
🇳🇬 *Welcome to Nigerian Tax Deadlines Bot*

Based on the Nigeria Tax Act 2025 and Tax Administration Act 2025.

I'll help you track tax deadlines and send you timely reminders!

*Select your category:*
"""
    
    keyboard = [
        [InlineKeyboardButton("👤 Individual", callback_data='cat_individual')],
        [InlineKeyboardButton("📈 Small Business (≤₦100M)", callback_data='cat_smallBusiness')],
        [InlineKeyboardButton("🏢 Company (>₦100M)", callback_data='cat_company')],
        [InlineKeyboardButton("📋 View All Categories", callback_data='view_all')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    category = get_user_category(chat_id)
    
    if not category:
        await update.message.reply_text('Please select your category first using /start')
        return
    
    await send_deadlines(chat_id, category, context)

async def change_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👤 Individual", callback_data='cat_individual')],
        [InlineKeyboardButton("📈 Small Business", callback_data='cat_smallBusiness')],
        [InlineKeyboardButton("🏢 Company", callback_data='cat_company')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text('Select your new category:', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """
📚 *Nigerian Tax Deadlines Bot - Help*

*Available Commands:*
/start - Register and select your category
/deadlines - View all deadlines for your category
/change - Change your taxpayer category
/test - Test reminder system NOW
/help - Show this help message

*Categories:*
👤 *Individual* - PIT, CGT, PAYE
📈 *Small Business* - Turnover ≤₦100M, Assets ≤₦250M
🏢 *Company* - Turnover >₦100M or Assets >₦250M

*Features:*
✅ View registration, filing & remittance deadlines
✅ See penalties for late compliance
✅ Automatic reminders before deadlines
✅ Based on Nigeria Tax Act 2025

*Need to update your category?*
Use /change to switch categories anytime.
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def test_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test the reminder system immediately"""
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔍 Testing reminder system now...\n\nCheck your logs and I'll send any applicable reminders.")
    await check_deadlines(context)
    await update.message.reply_text("✅ Reminder check complete! Check above for any reminders.")

# ============= CALLBACK HANDLER =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    data = query.data
    
    if data.startswith('cat_'):
        category = data.replace('cat_', '')
        add_user(chat_id, category)
        
        category_data = TAX_DEADLINES[category]
        confirm_message = f"""
✅ *Category Set: {category_data['name']}*

{category_data['description']}

You'll receive reminders for all applicable deadlines.

Use /deadlines to view all your tax obligations.
"""
        
        await query.message.reply_text(confirm_message, parse_mode='Markdown')
        
        # Automatically show deadlines
        await send_deadlines(chat_id, category, context)
        
    elif data == 'view_all':
        await send_all_categories(chat_id, context)

# ============= DEADLINE DISPLAY FUNCTIONS =============

async def send_deadlines(chat_id, category, context):
    data = TAX_DEADLINES[category]
    
    message = f"{data['name']}\n"
    message += f"{data['description']}\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for index, obligation in enumerate(data['obligations'], 1):
        message += f"*{index}. {obligation['title']}*\n"
        message += f"📋 Tax Type: {obligation['taxType']}\n"
        message += f"📅 Due Date: {obligation['dueDate']}\n"
        
        if 'description' in obligation:
            message += f"ℹ️ {obligation['description']}\n"
        
        message += f"⚠️ Penalty: {obligation['penalty']}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += "\n💡 You'll receive automatic reminders before each deadline."
    
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def send_all_categories(chat_id, context):
    message = "📊 *All Tax Categories - Nigeria Tax Act 2025*\n\n"
    
    for key, data in TAX_DEADLINES.items():
        message += f"{data['name']}\n"
        message += f"{data['description']}\n"
        message += f"Total Obligations: {len(data['obligations'])}\n\n"
    
    message += "Use /start to select your category and get personalized reminders."
    
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

# ============= REMINDER SYSTEM =============

async def send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id, obligation, days_left):
    urgency = '🚨 URGENT' if days_left <= 1 else '⚠️ IMPORTANT' if days_left <= 3 else '📢 REMINDER'
    day_text = 'TOMORROW' if days_left == 1 else 'TODAY' if days_left == 0 else f'in {days_left} days'
    
    message = f"""
{urgency}: Tax Deadline Approaching!

*{obligation['title']}*
📋 Tax Type: {obligation['taxType']}
📅 Due: {obligation['dueDate']}
⏰ Deadline: {day_text.upper()}

{obligation.get('description', '')}

⚠️ *Penalty for Late Compliance:*
{obligation['penalty']}

Don't miss this deadline! ⏱️
"""
    
    try:
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending reminder to {chat_id}: {e}")

async def check_deadlines(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running deadline check...")
    
    today = datetime.now()
    month = today.month
    day = today.day
    
    users = load_users()
    logger.info(f"Checking deadlines for {len(users)} users")
    
    for user in users:
        if not user.get('active') or not user.get('category'):
            logger.info(f"Skipping inactive user: {user.get('chatId')}")
            continue
        
        category = user['category']
        category_data = TAX_DEADLINES[category]
        logger.info(f"Checking {category} deadlines for user {user['chatId']}")
        
        for obligation in category_data['obligations']:
            if not obligation.get('recurring'):
                continue
            
            # Check annual deadlines (like 31 January or 18 December)
            if 'month' in obligation and 'day' in obligation:
                deadline_date = datetime(today.year, obligation['month'], obligation['day'])
                
                # If deadline has passed this year, check next year
                if deadline_date < today:
                    deadline_date = datetime(today.year + 1, obligation['month'], obligation['day'])
                
                diff_days = (deadline_date.date() - today.date()).days
                
                logger.info(f"Obligation: {obligation['title']}, Days until deadline: {diff_days}, Reminder days: {obligation.get('reminderDays', [])}")
                
                if diff_days in obligation.get('reminderDays', []):
                    logger.info(f"Sending reminder to {user['chatId']} for {obligation['title']}")
                    await send_reminder(context, user['chatId'], obligation, diff_days)
            
            # Check monthly deadlines (like 14th, 21st)
            if 'monthlyDay' in obligation:
                target_day = obligation['monthlyDay']
                days_until = target_day - day
                
                logger.info(f"Monthly obligation: {obligation['title']}, Days until: {days_until}, Reminder days: {obligation.get('reminderDays', [])}")
                
                if days_until >= 0 and days_until in obligation.get('reminderDays', []):
                    logger.info(f"Sending monthly reminder to {user['chatId']} for {obligation['title']}")
                    await send_reminder(context, user['chatId'], obligation, days_until)

# ============= MAIN =============

def main():
    logger.info("Starting Nigerian Tax Deadlines Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("deadlines", deadlines))
    application.add_handler(CommandHandler("change", change_category))
    application.add_handler(CommandHandler("test", test_reminders))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Schedule daily deadline check at 9 AM
    job_queue = application.job_queue
    
    # Parse the time string properly
    reminder_time = datetime.strptime("08:00", "%H:%M").time()
    job_queue.run_daily(check_deadlines, time=reminder_time)
    
    logger.info(f"✅ Scheduled daily reminders at {reminder_time}")
    logger.info("✅ Bot started successfully!")
    logger.info("Send /start to your bot to begin.")
    logger.info("Use /test to test reminders immediately.")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()