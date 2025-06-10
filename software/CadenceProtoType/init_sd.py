
# import os

# def initialize_sd():
#     # Create necessary directories if they don't exist
#     try:
#         os.mkdir("/sd/data")
#     except OSError:
#         pass  # Directory already exists
    
#     # Create CSV files with headers if they don't exist
#     files = [
#         ("payload_raw.csv", "timestamp,raw_value\n"),
#         ("payload_processed.csv", "timestamp,processed_value\n")
#     ]
    
#     for filename, header in files:
#         full_path = f"/sd/data/{filename}"
#         try:
#             # Try to open the file in read mode to check existence
#             with open(full_path, "r"):
#                 pass  # File exists, do nothing
#         except OSError:
#             # File doesn't exist, create it with header
#             with open(full_path, "w") as f:
#                 f.write(header)

# # Run the initialization when imported
# initialize_sd()