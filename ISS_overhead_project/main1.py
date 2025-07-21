import requests
import time
import math
import smtplib
import ssl
import os  # For environment variables

# --- Configuration ---
# You can get your current latitude and longitude from websites like https://www.latlong.net/
MY_LAT = 26.5458  # Example: Your Latitude
MY_LONG = 77.0197  # Example: Your Longitude

# Adjust the time difference for your time zone if needed.
# For Hindaun, Rajasthan, India, the timezone is IST (UTC+5:30).
TIME_DIFFERENCE_UTC_TO_LOCAL = 5.5  # For IST (UTC+5:30)

# Email Configuration
# IMPORTANT: DO NOT HARDCODE YOUR EMAIL PASSWORD DIRECTLY IN THE SCRIPT.
# Use environment variables for security.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")  # Your sending email address
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")  # The recipient email address
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Your app-specific password

SMTP_SERVER = "smtp.gmail.com"  # For Gmail. Change if using a different provider.
SMTP_PORT = 587  # TLS Port

# --- Constants ---
ISS_API_URL = "http://api.open-notify.org/iss-now.json"
SUNRISE_SUNSET_API_URL = "https://api.sunrise-sunset.org/json"


# --- Functions ---

def get_iss_location():
    """Fetches the current latitude and longitude of the ISS."""
    try:
        response = requests.get(ISS_API_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        iss_latitude = float(data["iss_position"]["latitude"])
        iss_longitude = float(data["iss_position"]["longitude"])
        return iss_latitude, iss_longitude
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ISS location: {e}")
        return None, None


def get_sunrise_sunset_times(latitude, longitude):
    """Fetches sunrise and sunset times for a given location."""
    params = {
        "lat": latitude,
        "lng": longitude,
        "formatted": 0  # Get times in UTC
    }
    try:
        response = requests.get(SUNRISE_SUNSET_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        sunrise_utc = int(data["results"]["sunrise"].split("T")[1].split(":")[0])
        sunset_utc = int(data["results"]["sunset"].split("T")[1].split(":")[0])
        return sunrise_utc, sunset_utc
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sunrise/sunset times: {e}")
        return None, None


def is_iss_overhead(my_lat, my_long, iss_lat, iss_long):
    """Checks if the ISS is within a certain range of your location."""
    if math.fabs(my_lat - iss_lat) < 5 and math.fabs(my_long - iss_long) < 5:
        return True
    return False


def is_night(sunrise_utc, sunset_utc, current_utc_hour):
    """Checks if it's currently dark at your location."""
    if sunrise_utc is None or sunset_utc is None:
        return True  # Assume night if we can't get sunrise/sunset

    if sunset_utc < sunrise_utc:
        return current_utc_hour >= sunset_utc or current_utc_hour < sunrise_utc
    else:
        return current_utc_hour >= sunset_utc and current_utc_hour < sunrise_utc


def send_iss_notification_email(sender_email, receiver_email, password, iss_lat, iss_long):
    """Sends an email notification that the ISS is overhead and visible."""
    subject = "🚀 ISS Overhead Notification! Look Up! 🛰️"
    body = f"""
The International Space Station is currently overhead and visible from your location!

**Location Details:**
Your Latitude: {MY_LAT}
Your Longitude: {MY_LONG}

ISS Latitude: {iss_lat:.2f}
ISS Longitude: {iss_long:.2f}

Time to go outside and spot it!
"""
    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)  # Secure the connection
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("Please check your email configuration, app password, and network connection.")


# --- Main Program ---
def main():
    print("🚀 ISS Overhead Notifier Started! 🚀")
    print(f"Monitoring your location: Latitude {MY_LAT}, Longitude {MY_LONG}")

    # Check if email credentials are set
    if not SENDER_EMAIL or not RECEIVER_EMAIL or not EMAIL_PASSWORD:
        print(
            "\n⚠️ WARNING: Email credentials (SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD) are not set as environment variables.")
        print("Email notifications will not be sent. Please set them for email functionality.")
        send_emails = False
    else:
        print(f"Email notifications will be sent from {SENDER_EMAIL} to {RECEIVER_EMAIL}.")
        send_emails = True

    # Flag to prevent sending multiple emails for the same pass
    email_sent_for_current_pass = False

    while True:
        iss_latitude, iss_longitude = get_iss_location()

        if iss_latitude is not None and iss_longitude is not None:
            print(f"Current ISS Location: Lat {iss_latitude:.2f}, Long {iss_longitude:.2f}")

            if is_iss_overhead(MY_LAT, MY_LONG, iss_latitude, iss_longitude):
                print("✨ The ISS is currently within range of your location! ✨")

                sunrise_utc, sunset_utc = get_sunrise_sunset_times(MY_LAT, MY_LONG)
                current_utc_hour = time.gmtime().tm_hour

                if is_night(sunrise_utc, sunset_utc, current_utc_hour):
                    print("🌃 It's dark outside, so the ISS should be visible! 🌃")
                    print("🔔 ISS IS OVERHEAD AND VISIBLE! Time to look up! 🔔")
                    if send_emails and not email_sent_for_current_pass:
                        send_iss_notification_email(SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD, iss_latitude,
                                                    iss_longitude)
                        email_sent_for_current_pass = True  # Set flag to true after sending
                else:
                    print("☀️ It's daytime, so the ISS won't be visible. ☀️")
                    email_sent_for_current_pass = False  # Reset flag if it's daytime now
            else:
                print("The ISS is not currently overhead.")
                email_sent_for_current_pass = False  # Reset flag if ISS is no longer overhead

        print("Waiting 60 seconds before checking again...")
        time.sleep(60)  # Check every 60 seconds


if __name__ == "__main__":
    main()