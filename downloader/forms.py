from django import forms

class GoogleDriveForm(forms.Form):
    drive_url = forms.URLField(label='Google Drive URL', required=True)
    destination_folder = forms.CharField(
        label='Destination Folder',
        required=True,
        widget=forms.HiddenInput()  # Hide this field from the user
    )