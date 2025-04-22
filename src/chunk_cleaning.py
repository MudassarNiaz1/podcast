from load_split_text import pdfloader,text_split
from dotenv import load_dotenv
from groq import Groq
import os
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq()

extracted_data=pdfloader
extracted_data=pdfloader(r"artifacts\\Attention-Is-All-You-Need.pdf")
text_chunks=text_split(extracted_data)
with open("Groq_Cleaned_Text.txt", "w", encoding="utf-8") as f:
    for i, chunk in enumerate(text_chunks):
        prompt = f"""
You are a world class text pre-processor, here is the raw data from a PDF, please parse and return it in a way that is crispy and usable to send to a podcast writer.

The raw data is messed up with new lines, Latex math and you will see fluff that we can remove completely. Basically take away any details that you think might be useless in a podcast author's transcript.

Remember, the podcast could be on any topic whatsoever so the issues listed above are not exhaustive.

Please be smart with what you remove and be creative ok?

Remember DO NOT START SUMMARIZING THIS, YOU ARE ONLY CLEANING UP THE TEXT AND RE-WRITING WHEN NEEDED.

Be very smart and aggressive with removing details, you will get a running portion of the text and keep returning the processed text.

PLEASE DO NOT ADD MARKDOWN FORMATTING, STOP ADDING SPECIAL CHARACTERS THAT MARKDOWN CAPITALISATION ETC LIKES.

ALWAYS start your response directly with processed text and NO ACKNOWLEDGEMENTS about my questions ok?And dont mention the line here is the processed text also create paragraphs while cleaning up the text.

Here is the text:
{chunk}
"""

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        cleaned_text = completion.choices[0].message.content
        print(cleaned_text)
        f.write(cleaned_text + "\n\n")
