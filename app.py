# %%writefile my_streamlit_app.py
import os
import subprocess
import tempfile

import requests
import streamlit as st
from scholarly import scholarly


class PDFLoader:
    def __init__(self, path):
        self.path = path

    def load_pdf(self):
        return self.path


def is_pdf(content):
    """Check if content is a PDF by examining the magic number."""
    return content.startswith(b'%PDF')


def download_pdf_urls(url_list, max_pdfs_to_keep=5):
    valid_pdfs = []
    temp_dir = tempfile.mkdtemp()  # Create a temporary directory to store downloaded files

    # Extract the URLs from the search results
    # url_list = [result['eprint_url'] for result in search_results if 'eprint_url' in result]

    try:
        for result in url_list:

            if 'eprint_url' in result:

                response = requests.get(result['eprint_url'])
                if response.status_code == 200:
                    content = response.content

                    if is_pdf(content):
                        # If it's a PDF, save it in the temporary directory
                        file_name = os.path.join(temp_dir, f"downloaded_{len(valid_pdfs) + 1}.pdf")
                        with open(file_name, 'wb') as pdf_file:
                            pdf_file.write(content)
                        valid_pdfs.append(file_name)
                        print(file_name)

                    # Stop when we have the desired number of valid PDFs
                    if len(valid_pdfs) >= max_pdfs_to_keep:
                        break

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    # clean up temporary files if needed
    for file_path in valid_pdfs:
        if os.path.exists(file_path):
            os.remove(file_path)

    # return the list of valid PDF file paths
    return valid_pdfs


# Initialize the embeddings model
embedding_model = ""

# LLM API endpoints
flask_app_url = 'https://chigger-safe-marmoset.ngrok-free.app/generate_llm_response'


def get_embeddings(docs, embedding_model):
    embedded_docs = 'embedding'
    return embedded_docs


def download_pdf(url):
    # Define the command as a list of strings
    command = ["wget", url]

    # Use subprocess to run the wget command
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def get_llm_response(question, context):
    # llm prompt
    prompt = f''''''

    payload = {"prompt": prompt}

    response = requests.post(flask_app_url, json=payload)

    if response.status_code == 200:

        response_data = response.json()

        answer = response_data['output'].replace(prompt, '').strip()
        st.markdown(
            f'<div style="background-color: #f3f3f3; padding: 10px; border-radius: 10px;">'
            f'<p style="font-size: 18px; font-weight: bold; color: #333;">Answer:</p>'
            f'<p style="font-size: 16px; color: #666;">{answer}</p>'
            f'</div>', unsafe_allow_html=True
        )
    else:
        st.write(f"Error: Unable to access the Flask app. \nStatus code: {response.status_code}")


def get_k_matched_docs(question, k):
    """Get the top k most semantically closest pages to the question"""
    return []


def get_context(doc_list):
    """This function returns the doc content in LLM friendly format"""
    return ''


def main():
    st.title("Document QA App")
    st.caption("Developed by Sagarika S")
    # files = st.file_uploader("Upload a pdf file", type=["pdf"], accept_multiple_files=True)

    # Initialize session state for vector db if not already set
    if 'db' not in st.session_state:
        st.session_state.db = None

    if 'files' not in st.session_state:
        st.session_state.files = None

    if 'search_string' not in st.session_state:
        st.session_state.search_string = None
    # if 'files' not in st.session_state:
    #     st.session_state.files = None

    with st.sidebar:

        if not st.session_state.files:

            search_string = st.sidebar.text_input("Search the Documents here",
                                                  placeholder="Search here",
                                                  help="""For example: Deep learning in text""")

            if search_string and (not st.session_state.files):
                st.sidebar.write(search_string)

                with st.spinner('Downloading PDFs, please wait...'):
                    # download PDFs
                    st.session_state.files = []
                    print(f"search_string = {search_string}")
                    search_results = scholarly.search_pubs(search_string, sort_by='relevance')
                    print(f"search_results = {search_results}")
                    st.session_state.files = download_pdf_urls(search_results, max_pdfs_to_keep=1)

    # Process PDFs and create FAISS database
    # if st.session_state.files and st.button("Process PDF"):
    if st.session_state.files and st.button("Process PDF", disabled=(not st.session_state.files)):
        with st.spinner('Processing, please wait...'):
            pdf_dict = {}
            for i, pdf_file_path in enumerate(st.session_state.files):
                try:

                    # load the pdf here
                    # loader = ()

                    loader = PDFLoader(pdf_file_path)

                    pages = loader.load_pdf()  # load the pages here

                    # key pdf_{i} represent the pdf file which the pages belong to
                    pdf_dict[f'pdf_{i}'] = pages

                except Exception as e:
                    st.write(f"An error occurred while processing the PDF: {e}")

            docs = [doc for pages_list in pdf_dict.values() for doc in pages_list]
            st.session_state.db = get_embeddings(docs, embedding_model=embedding_model)

    # Text input for question
    if st.session_state.files:
        st.write(st.session_state.files)

    question = st.text_input('Question:',
                             placeholder='What is the significance of PCA?',
                             disabled=not st.session_state.db,
                             help="""For example: Which is the best hotel?""")

    # Handle question querying
    if question and st.session_state.db:
        st.write(f"You asked: {question}")
        matched_docs_list = get_k_matched_docs(question, k=5)
        context = get_context(matched_docs_list)
        with st.spinner('Generating answer, please wait...'):
            get_llm_response(question, context)
            with st.expander("See context chunk"):
                st.write(context)

    if st.button("Reset", disabled=(bool(not st.session_state.files))):
        if 'db' in st.session_state:
            st.session_state.db = None

        if 'files' in st.session_state:
            st.session_state.files = []


if __name__ == '__main__':
    main()
