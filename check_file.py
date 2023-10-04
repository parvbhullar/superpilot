import os
import pandas as pd


def checkMerge(res_file_location, input_location, run_timestamp):
    data_df = pd.read_excel(input_location, sheet_name="WorkingSheet", header=1)
    data_df = data_df.reindex(columns=list(data_df.columns)[:6])

    final_data = pd.DataFrame([])
    for file in res_file_location:
        input_data = pd.read_csv(file, on_bad_lines="skip")
        final_data = pd.concat([input_data, final_data], axis=0)

    print(data_df.shape)
    print(final_data.shape)
    os.makedirs("Final", exist_ok=True)
    merge_files = pd.merge(data_df, final_data, how="left", on="Original Keyword")
    print(list(merge_files.columns))
    final_name = input_location.split("/")[-1]
    final_name, _ = os.path.splitext(final_name)
    final_name = f"Final/merge_files_{final_name}_Sheet_version_{run_timestamp}.csv"
    merge_files.to_csv(final_name, index=False)
