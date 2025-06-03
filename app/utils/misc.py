import os

def save_uploaded_file_to_disk(uploaded_file, folder="uploaded_docs"):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.read())
    return filepath