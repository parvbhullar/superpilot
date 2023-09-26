import pandas as pd

file_location = [
    "latex_response_20230926-181931.csv"
]

input_location = "/home/mastersindia/Documents/Personal/Knowledge/chat/superpilot/superpilot/docs/Copy of AI Answer 5M Scraping 2023-09-19 CB5.xlsx"
data_df = pd.read_excel(input_location, sheet_name="WorkingSheet", header=1)
data_df = data_df.reindex(columns=list(data_df.columns)[:6])

final_data = pd.DataFrame([])
for file in file_location:
    input_data = pd.read_csv(file)
    final_data = pd.concat([input_data, final_data], axis=0)

print(data_df.shape)
print(final_data.shape)

merge_files = pd.merge(data_df, final_data, how="left", on="Original Keyword")
print(list(merge_files.columns))
# merge_files.pop("Unnamed: 7")
merge_files.to_csv("Final/merge_files_CB5_Sheet_version.csv", index=False)
