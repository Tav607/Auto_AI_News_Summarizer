import argparse
import os
import dropbox
from dotenv import load_dotenv

def upload_to_dropbox(file_path, dbx):
    """Uploads a file to Dropbox."""
    try:
        file_name = os.path.basename(file_path)
        dropbox_path = f"/{file_name}"
        with open(file_path, "rb") as f:
            # Check file size, if > 150MB, use upload_session
            if os.path.getsize(file_path) > 150 * 1024 * 1024:
                print(f"File {file_name} is larger than 150MB, using chunked upload.")
                upload_session_start_result = dbx.files_upload_session_start(f.read(150 * 1024 * 1024))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
                
                while f.tell() < os.path.getsize(file_path):
                    if (os.path.getsize(file_path) - f.tell()) <= 150 * 1024 * 1024:
                        dbx.files_upload_session_finish(f.read(150 * 1024 * 1024), cursor, commit)
                    else:
                        dbx.files_upload_session_append_v2(f.read(150 * 1024 * 1024), cursor)
                        cursor.offset = f.tell()
            else:
                 dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))

        print(f"Successfully uploaded {file_name} to Dropbox path: {dropbox_path}")
    except dropbox.exceptions.ApiError as err:
        print(f"*** Dropbox API error: {err}")
        return None
    except Exception as e:
        print(f"*** Error uploading {file_path}: {e}")
        return None

def main():
    """Main function to handle argument parsing and file uploads."""
    # Load environment variables from .env file
    load_dotenv()
    dropbox_access_token = os.getenv("DROPBOX_ACCESS_TOKEN")

    if not dropbox_access_token:
        print("Error: DROPBOX_ACCESS_TOKEN must be set in .env file.")
        return

    # Setup argument parser
    parser = argparse.ArgumentParser(description="Upload files to Dropbox.")
    parser.add_argument('files', nargs='+', help='List of files to upload.')
    args = parser.parse_args()

    try:
        dbx = dropbox.Dropbox(dropbox_access_token)
        dbx.users_get_current_account()
        print("Successfully connected to Dropbox.")
    except Exception as e:
        print(f"Error connecting to Dropbox: {e}")
        return

    for file_path in args.files:
        if os.path.exists(file_path):
            upload_to_dropbox(file_path, dbx)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main() 