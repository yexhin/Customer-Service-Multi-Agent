from datetime import datetime
import dateparser


# Parse the time
def timeConvert(time_str: str,
               format: str = "%d.%m.%Y %H:%M"):
    try:
        date_parsed = datetime.strptime(time_str, format)
        return date_parsed
    except Exception:
        date_parsed = dateparser.parse(time_str)
        if not date_parsed:
            raise ValueError(f"Invalid time format: {time_str}")
    
    return date_parsed.strftime(format)
    
def timeParse(time_str: str, format: str = "%d.%m.%Y %H:%M") -> datetime:
    return datetime.strptime(time_str, format)
    
# Check the interval between delivery time and purchase time
def checkOrderValid(purchased_time: str, 
                    delivery_time: str) -> dict:
    # order_time = datetime.strptime(purchased_time, "%d.%m.%Y %H:%M")
    # deli_time = datetime.strptime(delivery_time, "%d.%m.%Y %H:%M")  
    
    order_time = timeParse(purchased_time)
    deli_time = timeParse(delivery_time)

    interval = (deli_time - order_time).total_seconds() / 3600
    
    if deli_time.hour in range(10, 21):
        if interval >= 4:
            return {"valid": True,
                    "message": "I saved your order. Cookies will come to your way right away with all our love (ෆ˙ᵕ˙ෆ)♡."}
        return {"valid": False,
                "message": "Sorry. Since we would like to present you our qualified cookies, the orders have to be placed at least 4 hours in advance ( •̯́ ^ •̯̀)."}
    else:
        return {
            "valid": False,
            "message": "Sorry, orders must be placed between 10:00 and 21:00."
        }

# Check refund
def checkRefund(purchased_time: str,
                delivery_time: str):
    try:
        # deli_time = datetime.strptime(order["delivery_time"], "%d.%m.%Y %H:%M")
        deli_time = timeConvert(delivery_time)
    except Exception:
        return {"status": "error", 
                "message": "Delivery time format invalid."}

    interval = (deli_time - datetime.now()).total_seconds() / 3600

    if interval >= 3:
        return {
            "status": True,
            "message": f"Refund approved."
        }
    else:
        return {
            "status": False,
            "message": f"Refund denied for order: cancellation too late."
        }