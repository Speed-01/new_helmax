import razorpay
import os
from dotenv import load_dotenv
import pathlib

# Get the absolute path to the .env file
base_dir = pathlib.Path(__file__).parent
env_path = base_dir / 'helmax' / '.env'

# Load environment variables
load_dotenv(env_path)

# Get Razorpay credentials
key_id = os.getenv('RAZORPAY_KEY_ID')
key_secret = os.getenv('RAZORPAY_KEY_SECRET')

print(f"Testing Razorpay connection with credentials:")
print(f"Key ID: {key_id}")
print(f"Key Secret: {key_secret[:4]}...{key_secret[-4:]}" if key_secret else "Key Secret: Not found")

try:
    # Initialize Razorpay client
    client = razorpay.Client(auth=(key_id, key_secret))
    print("Razorpay client initialized successfully")
    
    # Try to fetch orders to test connection
    print("Attempting to fetch orders...")
    try:
        orders = client.order.all()
        print("Connection successful! Orders retrieved.")
        
        # Try to create a test order
        print("\nAttempting to create a test order...")
        order_data = {
            "amount": 50000,  # amount in paise (₹500)
            "currency": "INR",
            "receipt": "test_receipt",
            "payment_capture": 1
        }
        order = client.order.create(data=order_data)
        print(f"Test order created successfully with ID: {order['id']}")
    except Exception as e:
        print(f"\nDetailed Error: {str(e)}")
        print(f"Error Type: {type(e).__name__}")
        
        # Try a simple API call to check authentication
        print("\nTrying a simple API call to check authentication...")
        try:
            balance = client.payment.fetch_all()
            print("Simple API call successful!")
        except Exception as e2:
            print(f"Simple API call failed: {str(e2)}")
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nPossible solutions:")
    print("1. Check if your Razorpay API keys are correct")
    print("2. Verify that your Razorpay account is active")
    print("3. Make sure you have the correct permissions")
    print("4. Check if your Razorpay package is up to date")