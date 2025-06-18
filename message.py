import requests

def send_message(message, title = 'Notification'):
    """
    Sends a message via HTTP POST request to a specified URL.

    Args:
        message (str): The message content to send. Defaults to 'pushText'.
    """
    url = "https://trigger.macrodroid.com/e887e811-f8db-4467-b256-651ad1f00f27/pushcelular"
    try:
        response = requests.get(f'{url}?pushTitle={title}&pushText={message}')
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Message sent successfully. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    # Example usage:
    # send_message("Hello from Python!")
    send_message('Teste') # Sends the default message 'pushText'
