from huggingface_hub import HfApi

repo_id = "fatma-omar/uniguide-model"
file_path = "rf_model_pipeline_pruned.pkl"
repo_path = "rf_model_pipeline.pkl"

token = input("Enter your Hugging Face write token (starts with hf_): ").strip()
api = HfApi(token=token)

print(f"Uploading {file_path} (38 MB) to {repo_id}/{repo_path}...")
api.upload_file(
    path_or_fileobj=file_path,
    path_in_repo=repo_path,
    repo_id=repo_id,
    repo_type="model",
)

print("\n Upload successful!")
