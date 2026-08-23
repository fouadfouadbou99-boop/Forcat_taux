import pandas as pd

def export_results(df, filename):

    with pd.ExcelWriter(
        filename,
        engine="xlsxwriter"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Results",
            index=False
        )
