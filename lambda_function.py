import os
import boto3
import psycopg2
import csv
from io import StringIO

def lambda_handler(event, context):
    # S3 details
    s3_bucket = 'amkadian-cf-templates--1obv518dn0xj-us-east-1'
    authors_key = 'authors.csv'
    books_key = 'books.csv'
    
    # RDS connection details
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = 5432

    # Download CSVs from S3
    s3 = boto3.client('s3')
    authors_obj = s3.get_object(Bucket=s3_bucket, Key=authors_key)
    books_obj = s3.get_object(Bucket=s3_bucket, Key=books_key)
    authors_csv = authors_obj['Body'].read().decode('utf-8')
    books_csv = books_obj['Body'].read().decode('utf-8')

    # Connect to RDS PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    cur = conn.cursor()

    # Insert authors
    author_id_map = {}
    reader = csv.DictReader(StringIO(authors_csv))
    for row in reader:
        cur.execute(
            "INSERT INTO authors (name, birth_year) VALUES (%s, %s) RETURNING author_id;",
            (row['name'], row['birth_year'])
        )
        author_id = cur.fetchone()[0]
        author_id_map[row['name']] = author_id

    # Insert books
    reader = csv.DictReader(StringIO(books_csv))
    for row in reader:
        author_id = author_id_map.get(row['author_name'])
        if author_id:
            cur.execute(
                "INSERT INTO books (title, author_id, published_year, genre) VALUES (%s, %s, %s, %s);",
                (row['title'], author_id, row['published_year'], row['genre'])
            )

    conn.commit()
    cur.close()
    conn.close()
    return {'status': 'success'}
