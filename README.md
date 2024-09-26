# AI-Driven DataStream Platform with Streamlit, S3 & SQL Integration

This project is a data processing and analysis pipeline that integrates various technologies including AWS S3, SQL Server, Streamlit, and OpenAI's API. It enables the storage, retrieval, and processing of both structured metadata and unstructured task files, and provides a user interface for interacting with these data sources.

## Overview

The project architecture consists of:

- **Python Modules**: Handle the interaction with RDBMS storage, object storage, metadata processing, and integration with the OpenAI API.
- **Object Storage**: Uses Amazon S3 for storing unstructured task files.
- **RDBMS Storage**: Uses Microsoft SQL Server to store structured metadata.
- **Streamlit App**: A user interface for uploading files, processing data, and viewing results.
- **OpenAI API**: Utilizes OpenAI's capabilities to analyze the unstructured data.

## Features

- **Upload Data to S3**: Upload task files to Amazon S3.
- **Upload Metadata to SQL Server**: Store metadata information in an SQL Server database.
- **Data Matching**: Match metadata with corresponding task IDs stored in S3.
- **Integration with OpenAI**: Send data to OpenAI for analysis and display results in the Streamlit app.
- **Streamlit Interface**: Interactive app for managing data uploads, processing, and analysis.

## Prerequisites

- Python 3.8+
- [Poetry](https://python-poetry.org/) for package management
- AWS credentials configured for access to S3
- Microsoft SQL Server instance
- OpenAI API key
- Streamlit installed (`pip install streamlit`)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
2. **Set up the Python environment:**
   ```bash
   poetry install
4. **Configure Environment Variables:**
   ```makefile
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   SQL_SERVER_CONNECTION_STRING=your_sql_server_connection_string
   OPENAI_API_KEY=your_openai_api_key
5. **Run the Streamlit App:**
   ```bash
   streamlit run streamlit_app.py

## File Structure

- aws_module.py: Contains functions to interact with AWS S3.
- sql_module.py: Handles interactions with the SQL Server for metadata storage.
- openai_module.py: Interfaces with the OpenAI API for data processing.
- streamlit_app.py: Main file to launch the Streamlit application.
- upload_data_to_s3.py: Script for uploading files to AWS S3.
- upload_metadata_rdb.py: Script for uploading metadata to the SQL Server.

## Usage

- Upload Data: Use the Streamlit app to upload task files and metadata.
- Data Processing: The backend Python modules handle the data processing and storage.
- Analyze with OpenAI: Send data to the OpenAI API for analysis and view results in the Streamlit app.
- Data Matching: Match metadata in SQL Server with task files in S3 for further processing.
