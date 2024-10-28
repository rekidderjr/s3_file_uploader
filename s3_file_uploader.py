"""
This module provides a script for uploading files from a local directory to an
Amazon S3 bucket. The script performs the following tasks:

1. Confirms the S3 bucket name and prefix, as well as the source directory.
2. Uploads files from the source directory to the S3 bucket, retrying on failure
   up to a maximum number of attempts.
3. Logs the details of each file upload (successful or failed) to a CSV log file.
4. Displays a summary of the file upload process, including the number of
   successful and failed uploads, and the location of the log file.

The script can be run as a standalone Python script. It requires the `boto3`
library to interact with the AWS S3 service.
"""

import os
import csv
import time
from datetime import datetime
import sys
import boto3

# Predefined folder and S3 bucket/prefix
if os.name == 'nt':  # Windows
    FOLDER_PATH = r"C:\Users\%USERNAME%\Documents\s3_upload"
else:  # macOS/Linux
    FOLDER_PATH = os.path.expanduser("~/Documents/s3_upload")
S3_BUCKET_NAME = "my_bucket"
S3_PREFIX = "s3_receive"
MAX_RETRIES = 3  # Maximum number of retries for file uploads

def main():
    """
    The main function that handles the file upload process.
    """
    # Create the S3 client
    s3 = boto3.client('s3')

    # Confirm the S3 bucket name and prefix
    confirm_s3_details(S3_BUCKET_NAME, S3_PREFIX)

    # Confirm the source directory
    confirm_source_dir(FOLDER_PATH)

    # Upload files from the folder to the S3 bucket, creating a new log file
    # for each upload
    uploaded_files, failed_files, log_file_path = upload_files_to_s3(
        FOLDER_PATH, S3_BUCKET_NAME, S3_PREFIX, s3)

    if uploaded_files:
        print("Successful file transfers:")
        for filename, source, destination, status, start_time, end_time, \
                duration, file_size, validated in uploaded_files:
            if not filename.startswith('.'):
                print(f"Filename:\t{filename}")
                print(f"Source:\t\t{source}")
                print(f"Destination:\t{destination}")
                print(f"Status:\t\t{status}")
                print(f"Start Time:\t{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"End Time:\t{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Duration:\t{duration:.1f} seconds")
                print(f"File Size:\t{file_size}")
                print(f"Validated:\t{validated}")
                print()

    if failed_files:
        print("Failed file transfers:")
        for filename, source, destination, status, start_time, end_time, \
                duration, file_size, validated in failed_files:
            if not filename.startswith('.'):
                print(f"Filename:\t{filename}")
                print(f"Source:\t\t{source}")
                print(f"Destination:\t{destination}")
                print(f"Status:\t\t{status}")
                print(f"Start Time:\t{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"End Time:\t{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Duration:\t{duration:.1f} seconds")
                print(f"File Size:\t{file_size}")
                print(f"Validated:\t{validated}")
                print()

    print(f"Transfer summary: Uploaded "
          f"{len([f for f in uploaded_files if not f[0].startswith('.')])} files, "
          f"Failed {len([f for f in failed_files if not f[0].startswith('.')])} files, "
          f"Log file saved as {log_file_path}")

def confirm_s3_details(s3_bucket_name, s3_prefix):
    """
    Confirms the S3 bucket name and prefix.
    """
    print(f"S3 bucket name: {s3_bucket_name}")
    print(f"S3 prefix: {s3_prefix}")
    confirmation = input("Is this information correct? (y/n) ")
    if confirmation.lower() != "y":
        print("Please update the script with the correct S3 bucket name "
              "and prefix.")
        exit(1)

def confirm_source_dir(folder_path):
    """
    Confirms the source directory.
    """
    print(f"Source directory: {folder_path}")
    confirmation = input("Is this information correct? (y/n) ")
    if confirmation.lower() != "y":
        print("Please update the script with the correct source directory.")
        exit(1)

def upload_files_to_s3(folder_path, s3_bucket_name, s3_prefix, s3):
    """
    Uploads files from the folder to the S3 bucket, creating a new log file
    for each upload.
    """
    logs_dir = os.path.join(folder_path, "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except OSError as e:
        if e.errno != 17:  # Ignore "File exists" error
            print(f"Error creating logs directory: {e}")
            return

    uploaded_files = []
    failed_files = []
    log_file_path = None

    for filename in os.listdir(folder_path):
        if not filename.startswith('.') and filename != 'logs':
            file_path = os.path.join(folder_path, filename)
            s3_key = f"{s3_prefix}/{filename}"
            log_file = os.path.join(logs_dir, f"log_"
                f"{datetime.now().strftime('%Y-%m-dT%H-%M-%S')}.csv")
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    start_time = datetime.now()
                    with open(file_path, 'rb') as file:
                        s3.upload_fileobj(file, s3_bucket_name, s3_key,
                                         Callback=ProgressPercentage(file,
                                                                    filename,
                                                                    s3_bucket_name,
                                                                    s3_key))
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    file_size = os.path.getsize(file_path)
                    validated = validate_file_upload(s3, s3_bucket_name, s3_key,
                                                    file_size)
                    log_file_path = write_to_log(log_file, filename, file_path,
                                                f"s3://{s3_bucket_name}/{s3_key}",
                                                'Uploaded', start_time, end_time,
                                                duration, file_size, validated)
                    uploaded_files.append((filename, file_path,
                                         f"s3://{s3_bucket_name}/{s3_key}",
                                         'Uploaded', start_time, end_time,
                                         duration, file_size, validated))
                    break  # Exit the retry loop if the upload is successful
                except boto3.exceptions.S3UploadFailedError as e:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    file_size = os.path.getsize(file_path)
                    log_file_path = write_to_log(log_file, filename, file_path,
                                                f"s3://{s3_bucket_name}/{s3_key}",
                                                'Failed', start_time, end_time,
                                                duration, file_size, 'No')
                    failed_files.append((filename, file_path,
                                        f"s3://{s3_bucket_name}/{s3_key}",
                                        'Failed', start_time, end_time,
                                        duration, file_size, 'No'))
                    print(f"Error uploading {filename}: {e}")
                    retries += 1
                    if retries < MAX_RETRIES:
                        print(f"Retrying upload for {filename} ({retries}/{MAX_RETRIES})")
                        time.sleep(5)  # Wait for 5 seconds before retrying
                    else:
                        print(f"Maximum retries reached for {filename}. "
                              "Skipping file.")
    return uploaded_files, failed_files, log_file_path

def write_to_log(log_file, filename, source, destination, status, start_time,
                 end_time, duration, file_size, validated):
    """
    Writes the file upload details to a log file.
    """
    header = ['Filename', 'Source', 'Destination', 'Status', 'Start Time',
              'End Time', 'Duration', 'File Size', 'Validated']
    rows = [[filename, source, destination, status,
             start_time.strftime('%Y-%m-%d %H:%M:%S'),
             end_time.strftime('%Y-%m-%d %H:%M:%S'),
             duration, file_size, validated]]

    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(rows)
    else:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)

    return log_file

def validate_file_upload(s3, s3_bucket_name, s3_key, file_size):
    """
    Validates the file upload by checking the content length.
    """
    try:
        obj = s3.head_object(Bucket=s3_bucket_name, Key=s3_key)
        if obj['ContentLength'] == file_size:
            return 'Yes'
        else:
            return 'No'
    except boto3.exceptions.S3UploadFailedError as e:
        print(f"Error validating {s3_key}: {e}")
        return 'No'

class ProgressPercentage(object):
    """
    A class to display the progress of file uploads.
    """
    def __init__(self, file_obj, filename, s3_bucket_name, s3_key):
        self._filename = filename
        self._file_obj = file_obj
        self._size = float(os.fstat(file_obj.fileno()).st_size)
        self._seen_so_far = 0
        self._s3_bucket_name = s3_bucket_name
        self._s3_key = s3_key

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        sys.stdout.write(
            f"\r{self._filename} {self._seen_so_far} / {self._size} ({percentage:.2f}%)")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
