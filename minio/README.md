# MinIO Configuration and Testing

This folder contains scripts and instructions to set up and verify MinIO as a data lake for storing raw Twitch data. MinIO provides scalable and reliable object storage for long-term data retention and replayability.

---

## **Folder Contents**

1. **`bucket-creation.py`**:

   - Creates necessary buckets in MinIO.
   - Ensures the bucket structure is ready before the pipeline processes data.

2. **`test-upload.py`**:

   - Verifies the ability to upload files to MinIO.
   - Confirms connectivity and access credentials are correctly set.

3. **`README.md`**:
   - Provides information and instructions for using these scripts.

---

## **Setup**

### **1. Prerequisites**

- MinIO must be running locally or on a server. Ensure the following settings:

  - **Endpoint**: `http://localhost:9000`
  - **Root User**: `admin`
  - **Root Password**: `admin123`

- Required Python libraries:
  ```bash
  pip install boto3
  ```

---

## **Usage**

### **1. Create Buckets**

Use `bucket-creation.py` to create the required buckets for the pipeline.

#### **Steps**:

1. Run the script:
   ```bash
   python bucket-creation.py
   ```
2. Expected output:
   - The `twitch-data` bucket is created in MinIO.
   - Any existing buckets are skipped to prevent overwriting.

---

### **2. Test File Upload**

Use `test-upload.py` to test uploading a sample file to MinIO.

#### **Steps**:

1. Run the script:
   ```bash
   python test-upload.py
   ```
2. Expected output:
   - The script generates a test JSON file and uploads it to the `twitch-data` bucket.
   - The uploaded file should appear in the MinIO console or can be verified programmatically.

---

## **Important Notes**

- Ensure MinIO credentials match the configuration in the scripts.
- Verify the `twitch-data` bucket exists before running the pipeline.
- For manual verification, open the MinIO console at `http://localhost:9001`.

---

## **Next Steps**

- After testing, use the `kafka_to_minio.py` script to automatically store raw Kafka data into MinIO.
- Process and validate the stored data using the `minio_to_postgres.py` script in the pipeline.
