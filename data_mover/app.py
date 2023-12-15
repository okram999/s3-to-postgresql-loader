import pg8000.native
import boto3
import json
from botocore.exceptions import ClientError

s3_src_bucket = "medigate-bucket-600669894233"
aws_region_name = "us-east-1"
target_db_table = "public.diabetes"

def get_secret():
    credential = {}
    secret_name = "medigate-demo"
    region_name = aws_region_name

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = json.loads(get_secret_value_response['SecretString'])

    credential['username'] = secret['username']
    credential['password'] = secret['password']
    credential['host'] = secret['host']
    credential['port'] = secret['port']
    credential['dbInstanceIdentifier'] = secret['dbInstanceIdentifier']
    print(credential)
    return credential



def lambda_handler(event, context):
    print(event)
    print("retrieving secrets")
    credential = get_secret()
    print("retrieving secrets done..")
    conn = pg8000.native.Connection(user=credential['username'], password=credential['password'], host=credential['host'], database="postgres", ssl_context=True)
    key = event["Records"][0]["s3"]["object"]["key"]
    query = f"SELECT aws_s3.table_import_from_s3('{target_db_table}','','(format csv, header true)',aws_commons.create_s3_uri('{s3_src_bucket}', '{key}', '{aws_region_name}'));"
    # query = "SELECT aws_s3.table_import_from_s3('public.diabetes','','(format csv, header true)',aws_commons.create_s3_uri('medigate-bucket-600669894233', 'diabetes_2.csv', 'us-east-1'));"
    res = conn.run(query)
    print(res)
    conn.close()
