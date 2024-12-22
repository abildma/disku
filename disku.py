import os
import concurrent.futures
import sys
import shutil

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
    print("\nChoose an option:")
    print("  1  Entire PC")
    print("  2  User folder")
    print("  3  External drives")
    print("  4  Search for file types")
    print("  q  Quit")
    print("  b  Back to previous scan")
    print("-" * 40)

# Function to format the size
def format_size(size):
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"

# Function to list external drives
def list_external_drives():
    external_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\") and os.path.ismount(f"{d}:\\")]
    print("\nExternal Drives:")
    for i, drive in enumerate(external_drives):
        print(f"  {i+1}. {drive}")
    print("-" * 40)
    return external_drives

# Function to scan the chosen directory
def scan_directory(directory_to_scan):
    # List to hold directory sizes and largest items
    directory_data = []
    dir_list = [os.path.join(directory_to_scan, dir) for dir in os.listdir(directory_to_scan) if os.path.isdir(os.path.join(directory_to_scan, dir))]
    total_dirs = len(dir_list)
    scanned_dirs = 0

    # Use ThreadPoolExecutor for multi-threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks to the executor
        futures = {executor.submit(process_directory, dir): dir for dir in dir_list}
        
        # Process the results as they complete and update progress
        for future in concurrent.futures.as_completed(futures):
            dir_name = futures[future]
            try:
                result = future.result()
                directory_data.append(result)
                scanned_dirs += 1
                progress = (scanned_dirs / total_dirs) * 100
                print(f"\rScanning... {progress:.2f}% complete", end="")
            except Exception as e:
                print(f"Error processing directory {dir_name}: {e}", file=sys.stderr)

    # Sort directories by size in descending order
    directory_data.sort(key=lambda x: x[1], reverse=True)

    # Print summary with numbered options for further exploration
    print("\n\nSummary:")
    for i, (directory, size, largest_item) in enumerate(directory_data):
        print(f"{i+1:>2}. {directory:<48} | {format_size(size):>10} | Largest Item: {largest_item[0]:<50} ({format_size(largest_item[1])})")
    print("-" * 40)

    return directory_data

# Function to search for files by type
def search_files_by_type(directory_to_scan, file_extension):
    matching_files = []
    for root, dirs, files in os.walk(directory_to_scan):
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(root, file)
                matching_files.append(file_path)
    return matching_files

# Function to delete a file or directory
def delete_item(item_path):
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)

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
                file_extension = input("Enter the file extension to search for (e.g., .txt): ")
                directory_to_scan = input("Enter the directory to search for file types (leave empty for entire PC): ") or "C:\\"
                matching_files = search_files_by_type(directory_to_scan, file_extension)
                print("\nMatching Files:")
                for file in matching_files:
                    print(file)
                print("-" * 40)
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
        print(f"\nScanning {directory_to_scan}...\n" + "-" * 40)
        directory_data = scan_directory(directory_to_scan)
        previous_scans.append(directory_data)

        # Prompt to explore a specific folder further
        while True:
            explore_option = input("Enter the number of the directory you want to explore further, 'd' to delete, 'b' to go back, or 'q' to quit: ")

            if explore_option.lower() == "q":
                print("Exiting program. Goodbye!")
                sys.exit()
            elif explore_option.lower() == "b":
                if previous_scans:
                    previous_scans.pop()  # Remove the current scan
                    if previous_scans:
                        directory_data = previous_scans.pop()
                        print("\nRestored previous scan:\n" + "-" * 40)
                        for i, (directory, size, largest_item) in enumerate(directory_data):
                            print(f"{i+1:>2}. {directory:<48} | {format_size(size):>10} | Largest Item: {largest_item[0]:<50} ({format_size(largest_item[1])})")
                    else:
                        break  # Exit the inner loop and go back to the main menu
                else:
                    break  # Exit the inner loop and go back to the main menu
            elif explore_option.lower() == "d":
                delete_choice = input("Enter the number of the item you want to delete: ")
                try:
                    delete_index = int(delete_choice) - 1
                    if 0 <= delete_index < len(directory_data):
                        item_to_delete = directory_data[delete_index][0]
                        confirm_delete = input(f"Are you sure you want to delete '{item_to_delete}'? (y/n): ")
                        if confirm_delete.lower() == "y":
                            delete_item(item_to_delete)
                            print(f"'{item_to_delete}' has been deleted.")
                            # Rescan the current directory
                            print(f"\nRescanning {directory_to_scan}...\n" + "-" * 40)
                            previous_scans.pop()  # Remove the current scan
                            directory_data = scan_directory(directory_to_scan)
                            previous_scans.append(directory_data)
                        else:
                            print("Deletion canceled.")
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            else:
                try:
                    explore_index = int(explore_option) - 1
                    if 0 <= explore_index < len(directory_data):
                        explore_directory = directory_data[explore_index][0]
                        print(f"\nScanning {explore_directory}...\n" + "-" * 40)
                        previous_scans.append(directory_data)
                        directory_data = scan_directory(explore_directory)
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
