from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sys
sys.path.append("..")
from db.database import Session, User, Bill, Outage, Log, Payment
from datetime import datetime
import re

class ActionListCommands(Action):
    def name(self) -> str:
        return "action_list_commands"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="🌟 Please select an option:\n1. Check My Bill\n2. Report Outage\n3. Sign Up\n4. Payment Status\n5. Support Ticket\n6. Service Plans\n7. About\n8. Goodbye\n(Or type the number/command, e.g., '1' or 'check my bill') 😊")
        return []

class ActionCheckBill(Action):
    def name(self) -> str:
        return "action_check_bill"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        phone = tracker.get_slot("phone")
        if not phone or not re.match(r'^07\d{8}$', phone):
            dispatcher.utter_message(text="🚫 Please enter a valid Kenyan phone number (e.g., 0712345678).")
            return [SlotSet("phone", None)]
        with Session() as session:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                bill = session.query(Bill).filter(Bill.user_id == user.id).first()
                if bill:
                    dispatcher.utter_message(text=f"✅ Your bill: {bill.amount} KES, due {bill.due_date.strftime('%Y-%m-%d')}, status: {bill.status}")
                else:
                    dispatcher.utter_message(text="🚫 No bill found. Please contact support.")
            else:
                dispatcher.utter_message(text="🚫 User not found. Please sign up.")
            session.add(Log(message=f"Checked bill for {phone}", timestamp=datetime.now()))
            session.commit()
        return [SlotSet("phone", None)]

class ActionReportOutage(Action):
    def name(self) -> str:
        return "action_report_outage"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        description = tracker.get_slot("outage_description") or tracker.latest_message.get("text", "").lower()
        with Session() as session:
            outage = Outage(description=description, start_time=datetime.now())
            session.add(outage)
            session.commit()
            dispatcher.utter_message(text=f"✅ Outage reported: {description}. We'll investigate soon! 🌱")
        return []

class ActionSignup(Action):
    def name(self) -> str:
        return "action_signup"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone")
        if not name:
            return [SlotSet("awaiting_name", True)]
        if not phone or not re.match(r'^07\d{8}$', phone):
            return [SlotSet("awaiting_phone", True)]
        with Session() as session:
            user = User(name=name, phone=phone)
            session.add(user)
            session.commit()
            dispatcher.utter_message(text=f"✅ Signup successful! Welcome, {name}! 😊")
            session.add(Log(message=f"Signed up: {name}, {phone}", timestamp=datetime.now()))
            session.commit()
        return [SlotSet("name", None), SlotSet("phone", None), SlotSet("awaiting_name", False), SlotSet("awaiting_phone", False)]

class ActionPaymentStatus(Action):
    def name(self) -> str:
        return "action_payment_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        phone = tracker.get_slot("phone")
        if not phone or not re.match(r'^07\d{8}$', phone):
            dispatcher.utter_message(text="🚫 Please enter a valid Kenyan phone number (e.g., 0712345678).")
            return [SlotSet("phone", None)]  # Re-prompt instead of falling back
        with Session() as session:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                payments = session.query(Payment).filter(Payment.user_id == user.id).all()
                total_paid = sum(p.amount for p in payments) if payments else 0
                last_payment = max((p.date for p in payments), default=datetime(1970, 1, 1))
                dispatcher.utter_message(text=f"✅ Payment history for {phone}: {total_paid} KES paid. Last payment: {last_payment.strftime('%Y-%m-%d')}. 🌱")
            else:
                dispatcher.utter_message(text="🚫 User not found. Please sign up.")
            session.add(Log(message=f"Checked payment status for {phone}", timestamp=datetime.now()))
            session.commit()
        return [SlotSet("phone", None)]

class ActionSupportTicket(Action):
    def name(self) -> str:
        return "action_support_ticket"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        phone = tracker.get_slot("phone") or tracker.get_slot("support_phone")
        description = tracker.get_slot("ticket_description") or tracker.latest_message.get("text", "").lower()
        if not phone or not re.match(r'^07\d{8}$', phone):
            dispatcher.utter_message(text="🚫 Please enter a valid Kenyan phone number (e.g., 0712345678).")
            return [SlotSet("support_phone", None)]  # Re-prompt instead of falling back
        with Session() as session:
            session.add(Log(message=f"Support ticket for {phone}: {description}", timestamp=datetime.now()))
            session.commit()
            dispatcher.utter_message(text=f"✅ Support ticket raised for {description}. Our team will contact you at {phone} soon! 🌿")
        return []

class ActionServicePlans(Action):
    def name(self) -> str:
        return "action_service_plans"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="🌟 Bayzinet Service Plans:\n1. Basic - 500 KES/mo (5 Mbps)\n2. Pro - 1000 KES/mo (10 Mbps)\n3. Premium - 2000 KES/mo (20 Mbps)\nReply with plan number to proceed! 😊")
        return []

class ActionAbout(Action):
    def name(self) -> str:
        return "action_about"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="🌟 About Bayzinet Customer Care Chatbot:\n- Built with: Rasa, FastAPI, MySQL, Twilio, pymysql, dotenv.\n- Developer: **Ericadesh**\n- Contact: 0741091661\nHappy to assist! 😊")
        return []