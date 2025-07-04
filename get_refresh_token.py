import dropbox

def get_refresh_token():
    """
    Helps generate a Dropbox refresh token.
    """
    app_key = input("Enter your Dropbox App Key: ").strip()
    app_secret = input("Enter your Dropbox App Secret: ").strip()

    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
        app_key,
        app_secret,
        token_access_type='offline'
    )

    authorize_url = auth_flow.start()
    print("\n1. Go to this URL in your browser and authorize the app:")
    print(authorize_url)
    print("\n2. Click 'Allow' (you might have to log in first).")
    print("3. Copy the authorization code shown on the screen.")

    auth_code = input("\\n4. Enter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
        print("\n✅ Success! Here are your credentials. Add them to your .env file.\n")
        print(f"DROPBOX_APP_KEY={app_key}")
        print(f"DROPBOX_APP_SECRET={app_secret}")
        print(f"DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
        print("\nYour old DROPBOX_ACCESS_TOKEN is no longer needed.")

    except Exception as e:
        print(f"\n❌ Error: An error occurred during authentication: {e}")

if __name__ == "__main__":
    get_refresh_token() 