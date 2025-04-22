from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
def pdfloader(file_path):
    loader = PyPDFLoader(file_path)
    extracted_data=loader.load()
    return extracted_data

def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 20)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks




