import openai
import pandas as pd
import uuid
import os

# Set your API key
openai.api_key = ""

# Define the function that generates dummy data
def generate_dummy_data(topic, num_rows=10, existing_data=None,):
    try:
        # Prepare prompt based on existing data if available
        prompt = f"Generate a table with {num_rows} rows of dummy data related to the topic '{topic}'."
        if existing_data is not None:
            prompt += f" Use the existing data below to guide the generation:\n{existing_data.head().to_csv(index=False)}"

        # Call the OpenAI API to generate data for the specified topic
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are a data generation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        # Extract the data from the response
        message = response['choices'][0].get('message', None)
        if not message:
            raise ValueError("No message found in the response.")

        data = message.get('content', '').strip()
        if not data:
            raise ValueError("No content found in the message.")

        # Process the data into a Pandas DataFrame
        lines = data.split('\n')
        headers = [header.strip() for header in lines[0].split('|')]
        rows = [row.split('|') for row in lines[1:num_rows+1]]
        df = pd.DataFrame(rows, columns=headers)
        df[input("enter the name of new_column: ")] = df.apply(lambda row: generate_new_column_value(row), axis=1)
        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def generate_new_column_value(row):
    # Example logic to generate a new column value based on existing columns
    # This should be customized based on the actual columns and desired logic
    # For demonstration, concatenating values of the first two columns
    try:
        return f"{row[0]}_{row[1]}"
    except IndexError:
        return "N/A"

def save_to_excel(df, filename, sheet_name='Sheet1'):
    # Check if the file exists
    if os.path.exists(filename):
        try:
            # Save the DataFrame to an existing Excel file
            with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Data saved to {filename} in sheet {sheet_name}.")
        except Exception as e:
            print(f"An error occurred while saving to Excel: {e}")
    else:
        try:
            # Save the DataFrame to a new Excel file
            df.to_excel(filename, index=False)
            print(f"Data saved to {filename}.")
        except Exception as e:
            print(f"An error occurred while creating the Excel file: {e}")

def main():
    print("Welcome to the Data Generation Tool!")
    
    while True:
        # Input the topic for which you want to generate data
        topic = input("Enter the topic: ")
        num_rows = int(input("Enter the number of rows: "))
        
        # Check if user wants to use existing data
        use_existing = input("Do you want to use existing data? (yes/no): ").strip().lower()
        excel_path = None
        if use_existing == 'yes':
            excel_path = input("Enter the path of the existing Excel file: ")
        
        if excel_path and os.path.exists(excel_path):
            try:
                # Load existing data from the provided Excel path
                existing_df = pd.read_excel(excel_path)
                # Generate new dummy data based on existing data
                df = generate_dummy_data(topic, num_rows, existing_df)
                # Generate a new dataset name
                dataset_name = f"{topic}_extended_data_{uuid.uuid4().hex}.xlsx"
                save_to_excel(df, dataset_name, sheet_name='NewData')
            except Exception as e:
                print(f"Failed to process existing data: {e}")
        else:
            # Generate dummy data without existing data
            df = generate_dummy_data(topic, num_rows)
            # Generate a random dataset name
            dataset_name = f"{topic}_dummy_data_{uuid.uuid4().hex}.xlsx"
            save_to_excel(df, dataset_name)
        
        # Ask if user wants to perform another operation
        another = input("Do you want to generate more data? (yes/no): ").strip().lower()
        if another != 'yes':
            print("Exiting the tool. Have a great day!")
            break

if __name__ == "__main__":
    main()
