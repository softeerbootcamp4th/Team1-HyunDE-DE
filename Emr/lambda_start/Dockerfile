FROM amazon/aws-lambda-python:3.8

RUN pip install pandas boto3 

COPY main.py ./

CMD [ "main.lambda_handler" ]