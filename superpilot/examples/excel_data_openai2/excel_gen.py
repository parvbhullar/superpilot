import openai
import pandas as pd
import uuid
import os

# Set your API key
openai.api_key = ""

# Function to generate a new column value for each row
def generate_new_column_value(row, column_name):
    try:
        row_data = row.to_dict()
        prompt = f"Based on the following row data, generate a value for the column '{column_name}': {row_data}"
        
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
        
        new_value = message.get('content', '').strip()
        if not new_value:
            raise ValueError("No content found in the message.")
        
        return new_value

    except Exception as e:
        print(f"An error occurred while generating the new column value: {e}")
        return "N/A"

# Function to generate dummy data
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

# Function to save the data to an Excel file
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

# Main function
def main():
    print("Welcome to the Data Generation Tool!")
    
    while True:
        topic = input("Enter the topic: ")
        num_rows = int(input("Enter the number of rows: "))
        
        use_existing = input("Do you want to use existing data? (yes/no): ").strip().lower()
        excel_path = None
        if use_existing == 'yes':
            excel_path = input("Enter the path of the existing Excel file: ")

        df = None
        if excel_path and os.path.exists(excel_path):
            try:
                existing_df = pd.read_excel(excel_path)
                # Ask user for the new column name
                new_column_name = input("Enter the name of the new column: ")
                # Generate values for the new column using the AI model
                existing_df[new_column_name] = existing_df.apply(lambda row: generate_new_column_value(row, new_column_name), axis=1)
                df = existing_df
                dataset_name = f"{topic}_extended_data_{uuid.uuid4().hex}.xlsx"
                save_to_excel(df, dataset_name, sheet_name='UpdatedData')
            except Exception as e:
                print(f"Failed to process existing data: {e}")
        else:
            df = generate_dummy_data(topic, num_rows)
            dataset_name = f"{topic}_dummy_data_{uuid.uuid4().hex}.xlsx"
            save_to_excel(df, dataset_name)

        another = input("Do you want to generate more data? (yes/no): ").strip().lower()
        if another != 'yes':
            print("Exiting the tool. Have a great day!")
            break

if __name__ == "__main__":
    main()
