from django.shortcuts import render, redirect
from .forms import GoogleDriveForm
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from io import FileIO
import os
import re

# Path to your credentials file
CREDENTIALS_FILE = 'credentials.json'

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def extract_file_or_folder_id(url):
    """
    Extract the file or folder ID from a Google Drive URL.
    Supports multiple URL formats.
    """
    # Standard file URL format
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # Folder URL format
    match = re.search(r'/drive/folders/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'folder'

    # Shortened URL format
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # Shared URL format
    match = re.search(r'/uc\?export=download&id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1), 'file'

    # If no match is found, raise an error
    raise ValueError("Invalid Google Drive URL. Could not extract file or folder ID.")


def download_file_from_google_drive(file_id, destination_folder):
    """Download a file from Google Drive using its file ID."""
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    try:
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata['name']

        # Create the destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)

        # Download the file in chunks
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(destination_folder, file_name)
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")

        return file_path
    except HttpError as e:
        raise Exception(f"Google Drive API error: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while downloading the file: {str(e)}")

def list_files_in_folder(folder_id):
    """List all files in a Google Drive folder."""
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    try:
        # Query files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        return files
    except HttpError as e:
        raise Exception(f"Google Drive API error: {str(e)}")
    except Exception as e:
        raise Exception(f"An error occurred while listing files: {str(e)}")

def download_view(request):
    if request.method == 'POST':
        form = GoogleDriveForm(request.POST)
        if form.is_valid():
            drive_url = form.cleaned_data['drive_url']
            destination_folder = form.cleaned_data['destination_folder']

            try:
                # Extract the ID and type (file or folder)
                resource_id, resource_type = extract_file_or_folder_id(drive_url)

                # Create the destination folder if it doesn't exist
                os.makedirs(destination_folder, exist_ok=True)

                if resource_type == 'file':
                    # Download a single file
                    file_path = download_file_from_google_drive(resource_id, destination_folder)
                    return render(request, 'downloader/success.html', {'file_path': file_path, 'destination_folder': destination_folder})
                elif resource_type == 'folder':
                    # List and download all files in the folder
                    files = list_files_in_folder(resource_id)
                    downloaded_files = []
                    for file in files:
                        file_path = download_file_from_google_drive(file['id'], destination_folder)
                        downloaded_files.append(file_path)
                    return render(request, 'downloader/success.html', {'file_paths': downloaded_files, 'destination_folder': destination_folder})
            except ValueError as e:
                return render(request, 'downloader/error.html', {'error': str(e)})
            except Exception as e:
                return render(request, 'downloader/error.html', {'error': f"An error occurred: {str(e)}"})
    else:
        form = GoogleDriveForm()
    return render(request, 'downloader/index.html', {'form': form})