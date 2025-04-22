from flask import Flask, request, render_template, send_file
import os
import PyPDF2
from model import generate_podcast

app = Flask(__name__)

# Set up a folder to store uploaded PDFs
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return render_template('index.html', error="No file part")

    uploaded_file = request.files['pdf_file']

    if uploaded_file.filename == '':
        return render_template('index.html', error="No selected file")

    if uploaded_file and uploaded_file.filename.endswith('.pdf'):
        try:
            # Save the uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(file_path)

            # Extract text from the PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

            # Save the extracted text to a file (optional)
            text_file = os.path.join(app.config['UPLOAD_FOLDER'], 'Groq_Cleaned_Text.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)

            # Generate the podcast with the extracted text
            output_file = generate_podcast(text)  # Pass the extracted text to your podcast generation function

            # Save the generated audio file in the static folder
            audio_file = os.path.join('static', 'generated_podcast.mp3')  # Update the path here if needed
            os.rename(output_file, audio_file)  # Assuming the generated file is output_file

            return render_template('index.html', audio_file='generated_podcast.mp3')

        except Exception as e:
            return render_template('index.html', error=f"Error processing the PDF: {e}")
    else:
        return render_template('index.html', error="Invalid file format. Please upload a PDF file.")

if __name__ == '__main__':
    app.run(debug=True)
