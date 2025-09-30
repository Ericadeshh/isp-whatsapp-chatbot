from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sys
sys.path.append("..")  # Add parent directory to path
from db.database import Session, User, Bill, Outage
from datetime import datetime

class ActionCheckBill(Action):
    def name(self) -> str:
        return "action_check_bill"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        phone = tracker.get_slot("phone")
        with Session() as session:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                bill = session.query(Bill).filter(Bill.user_id == user.id).first()
                if bill:
                    dispatcher.utter_message(text=f"Your bill: ${bill.amount}, due {bill.due_date.strftime('%Y-%m-%d')}, status: {bill.status}")
                else:
                    dispatcher.utter_message(text="No bill found. Please contact support.")
            else:
                dispatcher.utter_message(text="User not found. Please sign up.")
        return []

class ActionReportOutage(Action):
    def name(self) -> str:
        return "action_report_outage"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        description = tracker.get_slot("outage_description") or tracker.latest_message.get("text")
        with Session() as session:
            outage = Outage(description=description, start_time=datetime.now())
            session.add(outage)
            session.commit()
            dispatcher.utter_message(text=f"Outage reported: {description}. We'll investigate soon!")
        return []