# Directory Size & Cleanup Utility

## Overview
This Python program allows users to scan directories on their system, view the sizes of folders and files, and identify the largest files/folders. It also provides functionality to explore, delete, and rescan specific directories.

The program uses multi-threading to speed up directory scanning and includes several features such as viewing external drives, exploring subdirectories, and deleting unwanted files/folders.

## Features
- **Scan directories** on your system, external drives, or user folder.
- **Display directory sizes** and the largest file or folder within each directory.
- **Delete files and folders** directly from the interface.
- **Backtrack to previous scans** to explore different directories.
- **Multi-threaded scanning** for faster results on large directories.

## Requirements
- Python 3.6 or higher
- Standard Python libraries (no additional dependencies required)

## Usage

### Running the Program

1. **Choose the directory to scan**:
   Upon running the program, you will be presented with the following options:
   - `1`: Scan the entire PC (`C:\` drive)
   - `2`: Scan the user folder (`~/` on most systems)
   - `3`: Scan external drives connected to the system
   - `q`: Quit the program

2. **Scanning process**:
   - Once a directory is selected, the program will begin scanning the folder and its subdirectories.
   - It will list all the directories in the chosen location along with their sizes and the largest files/folders.

3. **Explore the results**:
   After the scan, you will have several options to interact with the results:
   - **View detailed directory info**: You can explore specific directories by choosing their number.
   - **Delete files or directories**: You can delete files/folders by selecting them and confirming the deletion.
   - **Back to previous scan**: If you want to go back and explore another part of the directory, you can do so by choosing 'b'.
   - **Quit the program**: You can exit the program by choosing 'q'.

### Commands:
- `1`: Scan the entire PC.
- `2`: Scan the user folder.
- `3`: Scan external drives.
- `q`: Quit the program.
- `b`: Go back to the previous scan.
- `d`: Delete a selected file or folder.

### Deleting Items:
If you select the option to delete an item, the program will ask for confirmation before proceeding. Once confirmed, the item will be deleted permanently.

## Example Output

When the program scans a directory, it might output something like the following:

```
Scanning C:\...

Summary:
 1. C:\Program Files (x86)\  | 12.45 GB   | Largest File: C:\Program Files (x86)\file1.txt     (5.67 GB)
 2. C:\Users\JohnDoe\Documents\ | 8.32 GB   | Largest File: C:\Users\JohnDoe\Documents\video.mp4  (4.12 GB)
 3. C:\Windows\System32\  | 6.70 GB   | Largest File: C:\Windows\System32\drivers\file.sys (3.45 GB)
----------------------------------------
Enter the number of the directory you want to explore further, 'd' to delete, 'b' to go back, or 'q' to quit:
```
