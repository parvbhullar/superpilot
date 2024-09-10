import openai
import pandas as pd
import uuid
import os
from io import StringIO

# Set your API key
openai.api_key = ""

#generate a new column for each row
def generate_new_column_value(row, column_name):
    try:
        row_data = row.to_dict()
        prompt = f"Based on the following row data, generate a value for the column '{column_name}': {row_data}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data generation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        message = response['choices'][0].get('message', None)
        if not message:
            raise ValueError("No message found in the response.")
        
        new_value = message.get('content', '').strip()
        if not new_value:
            raise ValueError("No content found in the message.")
        
        return new_value

    except Exception as e:
        print(f"An error occurred while generating the new column value: {e}")
        return "N/A"

def generate_more_rows(existing_data, num_rows=10):
    try:
        existing_data_csv = existing_data.to_csv(index=False)
        
        prompt = (f"Based on the following existing data, generate {num_rows} new unique rows of data. "
                  f"Ensure that the new rows are unique and do not duplicate any existing rows. "
                  f"Here is the existing data:\n{existing_data_csv}")
        
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are a data generation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        message = response['choices'][0].get('message', None)
        if not message:
            raise ValueError("No message found in the response.")
        
        new_data = message.get('content', '').strip()
        if not new_data:
            raise ValueError("No content found in the message.")
        
        # Convert the response to a DataFrame
        new_data_df = pd.read_csv(StringIO(new_data))
        
        return new_data_df

    except Exception as e:
        print(f"An error occurred while generating more rows: {e}")
        return pd.DataFrame()
    
def save_to_excel(df, filename, sheet_name='Sheet1'):
    if os.path.exists(filename):
        try:
            with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Data saved to {filename} in sheet {sheet_name}.")
        except Exception as e:
            print(f"An error occurred while saving to Excel: {e}")
    else:
        try:
            df.to_excel(filename, index=False)
            print(f"Data saved to {filename}.")
        except Exception as e:
            print(f"An error occurred while creating the Excel file: {e}")

def generate_dummy_data(topic, num_rows=10, existing_data=None):
    try:
        prompt = f"Generate a table with {num_rows} rows of dummy data related to the topic '{topic}'."
        if existing_data is not None:
            prompt += f" Use the existing data below to guide the generation:\n{existing_data.head().to_csv(index=False)}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are a data generation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        message = response['choices'][0].get('message', None)
        if not message:
            raise ValueError("No message found in the response.")
        
        data = message.get('content', '').strip()
        if not data:
            raise ValueError("No content found in the message.")
        
        lines = data.split('\n')
        headers = [header.strip() for header in lines[0].split('|')]
        rows = [row.split('|') for row in lines[1:num_rows+1]]
        df = pd.DataFrame(rows, columns=headers)

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Main function
def main():
    print("Welcome to the Data Generation Tool!")

    while True:
        use_existing = input("Do you want to use existing data? (yes/no): ").strip().lower()

        if use_existing == 'yes':
            existing_data_input = input("Paste the existing data (in CSV format) here: ")
            existing_data = pd.read_csv(StringIO(existing_data_input))

            num_rows = int(input("Enter the number of new rows to generate: "))
            new_data_df = generate_more_rows(existing_data, num_rows)
            #new column added here
            new_column_name = input("Enter the name of the new column (leave blank if not needed): ").strip()
            if new_column_name:
                new_data_df[new_column_name] = new_data_df.apply(lambda row: generate_new_column_value(row, new_column_name), axis=1)

            dataset_name = f"extended_data_{uuid.uuid4().hex}.xlsx"
            save_to_excel(new_data_df, dataset_name, sheet_name='ExtendedData')
        else:
            topic = input("Enter the topic for generating dummy data: ")
            num_rows = int(input("Enter the number of rows to generate: "))
            df = generate_dummy_data(topic, num_rows)

            dataset_name = f"{topic}_dummy_data_{uuid.uuid4().hex}.xlsx"
            save_to_excel(df, dataset_name)

        another = input("Do you want to generate more data? (yes/no): ").strip().lower()
        if another != 'yes':
            print("Exiting the tool. Have a great day!")
            break

if __name__ == "__main__":
    main()
