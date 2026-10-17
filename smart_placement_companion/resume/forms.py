from django import forms

class ResumeUploadForm(forms.Form):
    student_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    resume_file = forms.FileField(
        label="Upload PDF Resume",
        help_text="Only PDF files are supported.",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )
