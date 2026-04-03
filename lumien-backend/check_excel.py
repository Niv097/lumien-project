import pandas as pd

df = pd.read_excel(r'C:\Users\sapra\Desktop\LUMIEN\I4C_Simulated_Demo_Dataset.xlsx', sheet_name='Bank_Users')
print('Columns:', df.columns.tolist())
print('\nFirst 5 rows:')
print(df.head())
print('\nTotal rows:', len(df))
