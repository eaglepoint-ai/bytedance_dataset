from datetime import datetime, timedelta

# LEGACY GLOBAL - DO NOT CHANGE SIGNATURE
def save_to_db(user_id, status, expiry):
    print(f"SAVING: User {user_id} is now {status} until {expiry}")


class SubscriptionManager:
    def __init__(self, user_id, tier, status, expiry, balance):
        self.user_id = user_id
        self.tier = tier  # "FREE", "PREMIUM", "CORPORATE"
        self.status = status  # "ACTIVE", "EXPIRED", "PENDING"
        self.expiry = expiry
        self.balance = balance

    def process_tier_change(self, new_tier):
        now = datetime.now()

        # LOGIC 1: Pricing & Balance (Circular Dependency Potential)
        price = 0
        if new_tier == "PREMIUM":
            price = 100
        elif new_tier == "CORPORATE":
            price = 500

        if self.balance < price:
            raise Exception("Insufficient funds")

        # LOGIC 2: Transition Logic (The Downgrade Ghost)
        if self.tier == "PREMIUM" and new_tier == "FREE":
            # Keep premium perks until month end, but change billing status
            self.status = "ACTIVE"
            # Set expiry to last day of current month
            next_month = now.replace(day=28) + timedelta(days=4)
            self.expiry = next_month - timedelta(days=next_month.day)
        elif now > self.expiry and self.tier != "CORPORATE":
            self.status = "EXPIRED"
        else:
            self.status = "ACTIVE"
            self.expiry = now + timedelta(days=30)

        # LOGIC 3: Finalization
        self.tier = new_tier
        self.balance -= price

        # REQUIREMENT 1: Must call this
        save_to_db(self.user_id, self.status, self.expiry)

    def can_access_feature(self, feature_name):
        # Feature Access Logic
        if self.tier == "FREE" and feature_name in ["HD_VIDEO", "AD_FREE"]:
            return False
        if self.status == "EXPIRED":
            return False
        return True
