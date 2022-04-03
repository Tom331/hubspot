import time
from pip._vendor import requests


# Create companies, tasks, and associations. 
# I'm not doing it using the Bulk API because we need the ID of the company in order to associate a task with it.
def createCompanyAndTask(company, task):
    import hubspot
    from pprint import pprint
    from hubspot.crm.companies import BatchInputSimplePublicObjectInput, ApiException

    client = hubspot.Client.create(api_key=apiKey)

    batch_input_simple_public_object_input = BatchInputSimplePublicObjectInput(inputs=[
        {"properties": {
            "name": company.get('name'),
            "type": company.get('type'), # "Vendor" is a valid label, but not a valid value. Changing csv to use "VENDOR". Same with "PROSPECT"
            "hs_lead_status": company.get('status'), # PENDING IS NOT A VALID LEADSTATUS VALUE, updating CSV to use IN_PROGRESS instead
            "zip": company.get('postalCode'),
            }
        }])
    try:
        api_response = client.crm.companies.batch_api.create(
            batch_input_simple_public_object_input=batch_input_simple_public_object_input)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

    results = api_response.results
    result = results[0]
    companyId = result.id


    # Create task for company
    batch_input_simple_public_object_input = BatchInputSimplePublicObjectInput(inputs=[
        {"properties": {
            "hs_task_body": task.get('note'),
            "hs_timestamp": task.get('createdDate'),

            # There is no "Scheduled Date" property specified in the hubspot API for tasks. I see a "due date" field
            # when logged in and using the UI, but that doesn't seem to be available from the API.
            # So instead, i added the "Scheduled Date" column from the csv to the subject
            # source: https://developers.hubspot.com/docs/api/crm/tasks
            "hs_task_subject": 'Custom task. Due: ' + task.get('scheduledDate')
        }
        }])
    try:
        import pytz
        from datetime import datetime

        taskDatetime = datetime.strptime(task.get('createdDate'), "%d/%m/%Y %H:%M")
        utc_dt = taskDatetime.astimezone(pytz.utc)
        utc_string = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


        task = {"properties":
            {
                "hs_task_body": task.get('note'),
                "hs_timestamp": utc_string,

                # There is no "Scheduled Date" property specified in the hubspot API for tasks. I see a "due date" field
                # when logged in and using the UI, but that doesn't seem to be available from the API.
                # So instead, i added the "Scheduled Date" column from the csv to the subject
                # source: https://developers.hubspot.com/docs/api/crm/tasks
                "hs_task_subject": 'Custom task. Due: ' + task.get('scheduledDate')
            }
        }

        url = 'https://api.hubspot.com/crm/v3/objects/tasks?hapikey={removed for security}'
        req = requests.post(url, json=task) # POST request to create task
        taskId = req.json().get('id')

        # Create association from task to company:
        # I got "192" by retrieving the association type from the associations API
        url = 'https://api.hubspot.com/crm/v3/objects/tasks/' + taskId + '/associations/companies/' + companyId + '/192?hapikey={removed for security}'
        req = requests.put(url, json=task) # PUT request to create association



    except ApiException as e:
        print("Exception when calling task create: %s\n" % e)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # Auth
    from hubspot import HubSpot

    apiKey = '{removed for security}'

    api_client = HubSpot(api_key=apiKey)

    # Create objects from csv
    import csv
    with open('PYB data - ap_191121.csv') as f:
        reader = csv.reader(f)
        i = 0
        for row in reader:
            if i == 0:
                i = i + 1
                continue # skip first row of csv as it's a header
            # if i > 2:
            #     break # temp
            company = {'name': row[0], 'postalCode': row[1], 'type': row[2], 'status': row[3]}
            task = {'note': row[4], 'createdDate': row[5], 'scheduledDate': row[6]}
            createCompanyAndTask(company, task)

            i = i + 1
            if (i % 5) == 0:
                print(str(i) + ' rows done out of 45...') # 45 rows in spreadsheet


