import os

def list_files_and_contents(directory, output_file, include_all_files=True):
    if not os.path.exists(directory):
        print(f"❌ Error: Directory '{directory}' does not exist.")
        return

    print(f"📂 Scanning project: {directory}\n")

    with open(output_file, "w", encoding="utf-8") as f:
        for root, _, files in os.walk(directory):
            level = root.replace(directory, "").count(os.sep)
            indent = " " * 4 * level
            folder_name = f"{indent}{os.path.basename(root)}/\n"
            print(folder_name, end="")
            f.write(folder_name)

            for file in files:
                file_path = os.path.join(root, file)
                sub_indent = " " * 4 * (level + 1)
                file_name = f"{sub_indent}{file}\n"
                print(file_name, end="")
                f.write(file_name)

                if include_all_files or file.endswith(".py"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as file_content:
                            content = file_content.read()
                            formatted_content = f"\n{'='*50}\n{file_path}\n{'='*50}\n{content}\n\n"
                            print(formatted_content[:500])
                            f.write(formatted_content)
                    except Exception as e:
                        error_msg = f"Error reading {file_path}: {e}\n"
                        print(error_msg, end="")
                        f.write(error_msg)

# Add these lines at the bottom of the file:
if __name__ == "__main__":
    project_path = r"C:\Users\anand\Git\smart-search"  # Your project path
    output_file = "project_structure.txt"
    list_files_and_contents(project_path, output_file, include_all_files=True)