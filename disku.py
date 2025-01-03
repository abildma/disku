import os
import concurrent.futures
import sys
import shutil
import hashlib
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

# List of possible file types
file_types = [
    'txt', 'gif', 'html', 'jpeg', 'jpg', 'png', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'mp3', 'wav', 'mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv', 'zip', 'rar', '7z', 'tar', 'gz',
    'bmp', 'tiff', 'svg', 'ico', 'exe', 'dll', 'sys', 'bat', 'cmd', 'sh', 'py', 'java', 'class',
    'cpp', 'c', 'h', 'cs', 'js', 'ts', 'json', 'xml', 'csv', 'md', 'log', 'ini', 'cfg', 'conf'
]

# Function to suggest file extensions based on partial input
def suggest_file_extension(partial):
    suggestions = [ext for ext in file_types if ext.startswith(partial)]
    return suggestions

# Function to get the size of a directory and find the largest file/folder
def get_directory_size_and_largest(path):
    total_size = 0
    largest_item = ('', 0)  # (name, size)
    
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file():
                    size = entry.stat().st_size
                    total_size += size
                    if size > largest_item[1]:
                        largest_item = (entry.path, size)
                elif entry.is_dir(follow_symlinks=False):
                    dir_size, dir_largest_item = get_directory_size_and_largest(entry.path)
                    total_size += dir_size
                    if dir_size > largest_item[1]:
                        largest_item = (entry.path, dir_size)
            except OSError:
                pass
    except PermissionError:
        pass

    return total_size, largest_item

# Function to process a directory and return its size and largest item
def process_directory(directory):
    size, largest_item = get_directory_size_and_largest(directory)
    return directory, size, largest_item

# Function to display verbose output
def display_help():
    print("\n" + "-" * 104)
    print("Choose an option:")
    print("  1  Entire PC")
    print("  2  User folder")
    print("  3  External drives")
    print("  4  Search for file types")
    print("  q  Quit")
    print("  b  Back to previous scan")
    print("-" * 104)

# Function to display folder name instead of full path
def display_folder_name(full_path):
    folder_name = os.path.basename(full_path)
    print(f"Folder: {folder_name}")

# Function to format the size
def format_size(size):
    """Format the size to MB/GB."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# Function to list external drives
def list_external_drives():
    """
    Lists all mounted external drives.

    Returns:
        list: A list of external drive paths.
    """
    external_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\") and os.path.ismount(f"{d}:\\")]
    print("\n" + "-" * 104)
    print("External Drives:")
    for i, drive in enumerate(external_drives):
        print(f"  {i+1}. {drive}")
    print("-" * 104)
    return external_drives

# Function to scan the chosen directory
def scan_directory(directory_to_scan):
    """
    Scans the given directory and collects size and largest item information for each subdirectory.

    Args:
        directory_to_scan (str): The directory path to scan.

    Returns:
        list: A list of tuples containing directory data (path, size, largest item).
    """
    # List to hold directory sizes and largest items
    directory_data = []
    dir_list = [os.path.join(directory_to_scan, dir) for dir in os.listdir(directory_to_scan) if os.path.isdir(os.path.join(directory_to_scan, dir))]
    total_dirs = len(dir_list)
    scanned_dirs = 0

    # Print scanning message once
   # print(f"\nScanning {directory_to_scan}...\n")

    # Use ThreadPoolExecutor for multi-threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks to the executor
        futures = {executor.submit(process_directory, dir): dir for dir in dir_list}
        
        # Process the results as they complete and update progress
        for future in concurrent.futures.as_completed(futures):
            dir_name = futures[future]
            try:
                result = future.result()
                if result[1] > 0:  # Only include directories with size greater than 0
                    directory_data.append(result)
                scanned_dirs += 1
                progress = (scanned_dirs / total_dirs) * 100
       #         print(f"\rScanning... {progress:.2f}% complete", end="")
            except Exception as e:
                print(f"Error processing directory {dir_name}: {e}", file=sys.stderr)

    # Sort directories by size in descending order
    directory_data.sort(key=lambda x: x[1], reverse=True)

    return directory_data

# Function to search for files by type
def search_files_by_type(directory_to_scan, file_extension):
    """
    Searches for files with the given extension in the specified directory.

    Args:
        directory_to_scan (str): The directory path to search within.
        file_extension (str): The file extension to search for.

    Returns:
        list: A list of matching file paths.
    """
    matching_files = []
    for root, dirs, files in os.walk(directory_to_scan):
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(root, file)
                matching_files.append(file_path)
    return matching_files

# Function to delete a file or directory
def delete_item(item_path):
    """
    Deletes the specified file or directory.

    Args:
        item_path (str): The path of the file or directory to delete.
    """
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)

def truncate_name(name, length):
    """Truncate the name to a specified length."""
    if len(name) > length:
        return name[:length-3] + '...'
    return name

# Function to find duplicate files by extension
def find_duplicate_files_by_extension(directory_to_scan, file_extension):
    """
    Finds duplicate files with the given extension in the specified directory based on file size and hash.

    Args:
        directory_to_scan (str): The directory path to search within.
        file_extension (str): The file extension to search for.

    Returns:
        dict: A dictionary where the keys are file hashes and the values are lists of file paths.
    """
    file_hashes = {}
    for root, dirs, files in os.walk(directory_to_scan):
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                    if file_hash in file_hashes:
                        file_hashes[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = [file_path]
                except OSError:
                    pass
    duplicates = {hash: paths for hash, paths in file_hashes.items() if len(paths) > 1}
    return duplicates

# Function to summarize disk usage by file type
def summarize_by_file_type(directory_to_scan):
    """
    Summarizes disk usage by file type in the specified directory.

    Args:
        directory_to_scan (str): The directory path to scan.

    Returns:
        dict: A dictionary where the keys are file extensions and the values are total sizes.
    """
    file_type_summary = {}
    for root, dirs, files in os.walk(directory_to_scan):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()
            try:
                file_size = os.path.getsize(file_path)
                if file_extension in file_type_summary:
                    file_type_summary[file_extension] += file_size
                else:
                    file_type_summary[file_extension] = file_size
            except OSError:
                pass

    # Sort the summary by total size in descending order
    sorted_summary = dict(sorted(file_type_summary.items(), key=lambda item: item[1], reverse=True))
    return sorted_summary

def print_summary_in_columns(summary):
    """
    Prints the summary in a formatted way using multiple columns.

    Args:
        summary (dict): The summary dictionary to print.
    """
    items = list(summary.items())
    max_key_length = max(len(key) for key, _ in items)
    max_value_length = max(len(format_size(value)) for _, value in items)
    column_width = max_key_length + max_value_length + 5

    # Get the terminal width
    terminal_width = shutil.get_terminal_size().columns

    # Calculate the number of columns that can fit in the terminal width
    columns = max(1, terminal_width // column_width)

    for i in range(0, len(items), columns):
        row_items = items[i:i + columns]
        row_str = ""
        for key, value in row_items:
            row_str += f"{key:<{max_key_length}} {format_size(value):>{max_value_length}}".ljust(column_width)
        print(row_str)

# Function to capture user input with suggestions using prompt_toolkit
def input_with_suggestions(prompt_text):
    completer = WordCompleter(file_types, ignore_case=True)
    user_input = prompt(prompt_text, completer=completer)
    return user_input

if __name__ == "__main__":
    previous_scans = []

    while True:
        if not previous_scans:
            display_help()
            option = input("Enter your choice: ")

            if option == "1":
                directory_to_scan = "C:\\"
            elif option == "2":
                directory_to_scan = os.path.expanduser("~")
            elif option == "3":
                external_drives = list_external_drives()
                if not external_drives:
                    print("No external drives found.")
                    continue
                drive_choice = input("Enter the number of the external drive you want to scan: ")
                try:
                    drive_index = int(drive_choice) - 1
                    if 0 <= drive_index < len(external_drives):
                        directory_to_scan = external_drives[drive_index]
                    else:
                        print("Invalid number. Please try again.")
                        continue
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    continue
            elif option == "4":
                file_extension = input_with_suggestions("Enter the file extension to search for (e.g., .txt): ")
                directory_to_scan = input("Enter the directory to search for file types (leave empty for entire PC): ") or "C:\\"
                matching_files = search_files_by_type(directory_to_scan, file_extension)
                print("\n" + "-" * 104)
                print("Matching Files:")
                for file in matching_files:
                    print(file)
                print("-" * 104)
                continue
            elif option.lower() == "q":
                print("Exiting program. Goodbye!")
                sys.exit()
            else:
                print("Invalid option. Please try again.")
                continue
        else:
            directory_data = previous_scans.pop()

        # Scan the selected directory
        directory_data = scan_directory(directory_to_scan)
        previous_scans.append(directory_data)

        # Print summary with numbered options for further exploration
        print("\n\n" + "-" * 104)
        print(f"\nScanning {directory_to_scan}... \n")
        print("Enter the number of the directory you want to explore further")
        print("File extension search followed by number ex: txt1, py4, jpeg3")  
        print("'d' followed by a number to delete")
        print("'o' followed by a number to open in file explorer")
        print("'g' followed by a number to navigate to the largest folder")
        print("'f' followed by a number and file extension to find duplicate files (e.g., f1jpeg)")
        print("'s' followed by a number to summarize disk usage by file type")
        print("'b' to go back, or 'q' to quit:")
        print("-" * 104)
        print("Summary:")
        for i, (directory, size, largest_item) in enumerate(directory_data):
            # Extract current folder and subfolder
            relative_path = os.path.relpath(directory, directory_to_scan)
            # Extract the folder name from the largest item path
            largest_folder_name = os.path.basename(largest_item[0])
            print(f"{i+1:>2}. {relative_path:<30.30} | {format_size(size):>10} | Largest: {largest_folder_name:<30.30} | {format_size(largest_item[1]):>10} |")
        print("-" * 104)

        while True:
            explore_option = input()

            if explore_option.lower() == "q":
                print("Exiting program. Goodbye!")
                sys.exit()
            elif explore_option.lower() == "b":
                if previous_scans:
                    directory_data = previous_scans.pop()
                    print("\n" + "-" * 104)
                    print("Restored previous scan:")
                    for i, (directory, size, largest_item) in enumerate(directory_data):
                        directory_name = os.path.basename(directory)
                        largest_item_name = os.path.basename(largest_item[0])
                        print(f"{i+1:>2}. {truncate_name(directory_name, 30):<30} | {format_size(size):>10} | Largest: {truncate_name(largest_item_name, 30):<30} | {format_size(largest_item[1]):>10} |")
                else:
                    break  # Exit the inner loop and go back to the main menu
            elif explore_option.lower().startswith("d"):
                try:
                    delete_index = int(explore_option[1:]) - 1
                    if 0 <= delete_index < len(directory_data):
                        item_to_delete = directory_data[delete_index][0]  # Delete the directory itself
                        confirm_delete = input(f"Are you sure you want to delete '{item_to_delete}'? (y/n): ")
                        if confirm_delete.lower() == "y":
                            delete_item(item_to_delete)
                            print(f"'{item_to_delete}' has been deleted.")
                            # Rescan the current directory
                            directory_data = scan_directory(directory_to_scan)
                            previous_scans.append(directory_data)
                        else:
                            print("Deletion canceled.")
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            elif explore_option.lower().startswith("o"):
                try:
                    open_index = int(explore_option[1:]) - 1
                    if 0 <= open_index < len(directory_data):
                        item_to_open = directory_data[open_index][0]  # Open the directory itself
                        os.startfile(item_to_open)
                        print(f"Opened {item_to_open} in file explorer.")
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            elif explore_option.lower().startswith("g"):
                try:
                    goto_index = int(explore_option[1:]) - 1
                    if 0 <= goto_index < len(directory_data):
                        goto_folder = directory_data[goto_index][2][0]  # Navigate to the largest folder
                        print(f"Navigated to {goto_folder}")
                        previous_scans.append(directory_data)
                        directory_data = scan_directory(goto_folder)
                        directory_to_scan = goto_folder  # Update the current directory
                        break  # Exit the inner loop and go back to the main menu
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a valid number after 'g'.")
            elif explore_option.lower().startswith("f"):
                try:
                    search_index = int(''.join(filter(str.isdigit, explore_option))) - 1
                    file_extension = ''.join(filter(str.isalpha, explore_option[1:]))
                    if 0 <= search_index < len(directory_data):
                        search_directory = directory_data[search_index][0]
                        duplicates = find_duplicate_files_by_extension(search_directory, f".{file_extension}")
                        print("\n" + "-" * 104)
                        print(f"Duplicate Files for .{file_extension}:")
                        for file_hash, paths in duplicates.items():
                            print(f"Hash: {file_hash}")
                            for path in paths:
                                print(f"  {path}")
                        print("-" * 104)
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a valid number and file extension after 'f'.")
            elif explore_option.lower().startswith("s"):
                try:
                    search_index = int(explore_option[1:]) - 1
                    if 0 <= search_index < len(directory_data):
                        search_directory = directory_data[search_index][0]
                        file_type_summary = summarize_by_file_type(search_directory)
                        print("\n" + "-" * 104)
                        print("Disk Usage by File Type:")
                        print_summary_in_columns(file_type_summary)
                        print("-" * 104)
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a valid number after 's'.")
            else:
                try:
                    # Check if the input is a file type search command
                    if any(explore_option.lower().startswith(ext) for ext in file_types):
                        file_extension = ''.join(filter(str.isalpha, explore_option))
                        search_index = int(''.join(filter(str.isdigit, explore_option))) - 1
                        if 0 <= search_index < len(directory_data):
                            search_directory = directory_data[search_index][0]
                            matching_files = search_files_by_type(search_directory, f".{file_extension}")
                            print("\n" + "-" * 104)
                            print(f"Matching Files for .{file_extension}:")
                            for file in matching_files:
                                print(file)
                            print("-" * 104)
                        else:
                            print("Invalid number. Please try again.")
                    else:
                        explore_index = int(explore_option) - 1
                        if 0 <= explore_index < len(directory_data):
                            explore_directory = directory_data[explore_index][0]
                            previous_scans.append(directory_data)
                            directory_data = scan_directory(explore_directory)
                            directory_to_scan = explore_directory  # Update the current directory
                            break  # Exit the inner loop and go back to the main menu
                        else:
                            print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number or a valid file type search command.")