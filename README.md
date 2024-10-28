# S3 File Uploader

This project provides two scripts that allow you to upload files from a local folder to an S3 bucket:

1. `s3_file_uploader.py`: This is the main script that handles the file uploads, logging, and validation.
2. `ide_setup.sh`: This is a convenience script that sets up the development environment and runs the `s3_file_uploader.py` script.

## Features

- Uploads files from a predefined folder to a predefined S3 bucket and prefix.
- Logs the file transfer details (filename, source, destination, status, start time, end time, duration, file size, and validation status) to a `log.csv` file.
- Appends to the `log.csv` file instead of overwriting it.
- Handles errors during the file transfer and logs them in the `log.csv` file.
- Validates the uploaded files by checking their size on the S3 bucket and logs the validation status.

## Requirements

- Python 3.x
- The following Python libraries:
  - `boto3`
  - `tqdm`

See the `requirements.txt` file for the exact library versions.

## Setup

1. Ensure your host operating system is configured with the necessary AWS permissions to access the S3 bucket and perform the file uploads.

   The script requires the following permissions:

   - `s3:PutObject`
   - `s3:HeadObject`

   Here's a sample IAM policy that grants the required permissions:

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:PutObject",
                   "s3:HeadObject"
               ],
               "Resource": [
                   "arn:aws:s3:::my_bucket/*",
                   "arn:aws:s3:::my_bucket"
               ]
           }
       ]
   }

    
