# %%
# Import the required libraries
import pandas as pd
import numpy as np
from pandas_profiling import ProfileReport
import re

# %%
# Read the CSV table 
data_df = pd.read_csv("table-2.csv",header= None, sep = ";")

data_df

# %%
# show me data_df where 12 contains " VALDEGOBIA"
data_df[data_df[12].str.contains("VALDEGOVIA")]

# %%
# rename each column as a string as a number
data_df.columns = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

# %%
# Rename the columns and drop the useless columns
data_df = data_df.rename(columns={'0': 'Reference','1' : 'Owner', '2' :'NIF/CIF','3':'Registered office','4':'City','5':'Province','6':'Postal Code','7':'Concession opening', '8' : 'Concession termination'})
data_df = data_df.drop(['9', '10', '11'], axis=1)


# %% [markdown]
# # EXTRACT THE DATA FROM COLUMN 12

# %%


# %%
data_df['12'] = data_df['12'].str.replace(r'(\d+),(\d+)', r'\1.\2')

# %%
# split the column based on each time 'GHz' appears
data_df['12'] = data_df['12'].str.split('Hz')

# %%
# in the Owner Column delete everything after the first comma
data_df['Owner'] = data_df['Owner'].str.split(',').str[0]
#delete all the . from the owner column
data_df['Owner'] = data_df['Owner'].str.replace('.', '')
#delete all the characters that are not capital letters or spaces from the owner column
data_df['Owner'] = data_df['Owner'].str.replace('[^A-Z ]', '')
# in the owner column delete all groups of letter that are less than 4 characters
data_df['Owner'] = data_df['Owner'].str.replace(r'\b\w{1,3}\b', '')
# in the owner column reomve all the groups of characters starting with ESP
data_df['Owner'] = data_df['Owner'].str.replace(r'ESP[A-Z ]+', '')
# in the owner column remove all double spaces
data_df['Owner'] = data_df['Owner'].str.replace('  ', ' ')
# in the owner column remove "UNIPERSONAL"
data_df['Owner'] = data_df['Owner'].str.replace('UNIPERSONAL', '')
#in the owner column remove all the spaces at the beginning of the string
data_df['Owner'] = data_df['Owner'].str.lstrip()
data_df['Owner'] = data_df['Owner'].str.rstrip()

# %%
#show me a list of all the unique values in the Owner column
data_df['Owner'].unique()

# %%


# %%
data_df

# %%
# for each item in the list in column 12, take the first item in the list and create a new row with all the other columns the same
data_df1 = data_df.explode('12')
data_df1

# %%
data_df1

# %% [markdown]
# # DATA CLEANING

# %%
data_df1['Reference'] = data_df1['Reference'].str.extract('([A-Z].*)')

# %%
data_df1['12'] = data_df1['12'].str.extract('([0-9A-Z].*)')
data_df1

# %%
data_df2 = data_df1[data_df1['12'].notna()]


# %%
data_df2

# %%
# create a new column called 'Frequency' which goes through column 12 and only takes until the end if it begins with a number but if it begins with a letter, continue until the , and then take the rest of the string
data_df2['Frequency'] = data_df2['12'].str.extract('([0-9].*)')
data_df2

# %%



# %%

data_df2 = data_df2.rename(columns={'12': 'Municipality'})

# %%
# delete the last letter of the column 'Municipality'
data_df2['Municipality'] = data_df2['Municipality'].str[:-1]

# %%
#from the municipality column replace all the characters that are not letters or space by nothing
#data_df2['Municipality'] = data_df2['Municipality'].str.replace('[^a-zA-Z /]', '')
# from the municipality column replace all numbers , and . by nothing
data_df2['Municipality'] = data_df2['Municipality'].str.replace('[0-9.,]', '')



# %%
data_df2

# %%
#formatted_string = re.sub(r'^\((\w+)\)', r'\1\'', string)



# %%
data_df2.reset_index(inplace=True)

# %%


# %%


# %%
# Assigning the right Municipality value to all rows
for row in range(len(data_df2)):
    if len(data_df2['Municipality'][row]) == 0 :
        data_df2['Municipality'][row] = data_df2['Municipality'][row-1]
    else: 
        continue

# %%
# Duplicating the frequency column to avoid confusion, as we have two units MHZ and GHZ
data_df2["Frequency GHZ"] = data_df2["Frequency"]
for row in range(len(data_df2)):
    if "G" in data_df2['Frequency'][row]:
        data_df2['Frequency'][row] = 0
    else: 
        continue
        
for row in range(len(data_df2)):
    if "M" in data_df2['Frequency GHZ'][row]:
        data_df2['Frequency GHZ'][row] = 0
    else: 
        continue

# %%
# cleaning the two frequency columns to end up with only numerical values

data_df2['Frequency'] = data_df2['Frequency'].astype(str)
data_df2['Frequency GHZ'] = data_df2['Frequency GHZ'].astype(str)


def extract_numbers(string):
    return [float(x) if '.' in x else int(x) for x in re.findall(r'[-+]?\d*\.\d+|\d+', string)]

data_df2['Frequency'] = data_df2['Frequency'].apply(lambda x: extract_numbers(x))
data_df2['Frequency GHZ'] = data_df2['Frequency GHZ'].apply(lambda x: extract_numbers(x))

data_df2['Frequency'] = data_df2['Frequency'].str.get(-1)
data_df2['Frequency GHZ'] = data_df2['Frequency GHZ'].str.get(-1)

# %%
#in the municipality column replace xcx by N
data_df2['Municipality'] = data_df2['Municipality'].str.replace('xcx', 'N')

# %%
# in the municipality colum if there is / then take the first part of the string
data_df2['Municipality'] = data_df2['Municipality'].str.split('/').str[0]

# %%
# for all rows of the municipality column where the lenght of the string is 0, replace it by the value of the previous row
for row in range(len(data_df2)):
    if len(data_df2['Municipality'][row]) <= 1 :
        data_df2['Municipality'][row] = data_df2['Municipality'][row-1]
    else: 
        continue


# %%
# for the municipality column, delete all the spaces after the last letter
data_df2['Municipality'] = data_df2['Municipality'].str.rstrip()


# %%
data_df2

# %%
# for all the values not equal to 0 in the frequency column, divide by 1000 to get the frequency in GHZ and write this number in the frequency GHZ column withouth changing the values in the frequency column
for row in range(len(data_df2)):
    if data_df2['Frequency'][row] != 0:
        data_df2['Frequency GHZ'][row] = data_df2['Frequency'][row] / 1000
    else: 
        continue

# write exactly the same code as above but to transform GHZ from the frequency GHZ column to MHZ in the frequency column
for row in range(len(data_df2)):
    if data_df2['Frequency GHZ'][row] != 0:
        data_df2['Frequency'][row] = data_df2['Frequency GHZ'][row] * 1000
    else: 
        continue


# %%
# create a new column called frequency GHZ rounded to 0 decimal that is equal to the frequency GHZ colum but rounded to 0 decimal
data_df2['Frequency GHZ rounded'] = data_df2['Frequency GHZ'].round(0)


# %%
# create a column called last opened concession that is equal to the the last concession opening date by the corresponding owner 
data_df2['Last opened concession'] = data_df2.groupby('Owner')['Concession opening'].transform('max')


# %%
# create a column called number of concession that counts the number of concession owned by the corresponding owner
data_df2['Number of concession'] = data_df2.groupby('Owner')['Owner'].transform('count')


# %%
# create a column called # of concession in municipality that counts the number of concession preesent in the corresponding municipality
data_df2['# of concession in municipality'] = data_df2.groupby('Municipality')['Municipality'].transform('count')

# %%
#create a column # of owner in municipality that counts the number of owner present in the corresponding municipality
data_df2['# of owner in municipality'] = data_df2.groupby('Municipality')['Owner'].transform('nunique')

# %%
#what is the data type of the column frequency GZ rounded
data_df2['Frequency GHZ rounded'].dtype

# %%
# check if a Municipality includes "(L')" and if it does, add "L'" before the name of the municipality
for row in range(len(data_df2)):
    if "(L')" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "L'" + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(L')" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(L')", "")
    else: 
        continue

# %%
# check if a Municipality includes "(L')" and if it does, add "L'" before the name of the municipality
for row in range(len(data_df2)):
    if "(LA)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "LA " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(LA)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(LA)", "")
    else: 
        continue

# %%
# check if a Municipality includes "(L')" and if it does, add "L'" before the name of the municipality
for row in range(len(data_df2)):
    if "(EL)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "EL " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(EL)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(EL)", "")
    else: 
        continue

# %%
# check if a Municipality includes "(L')" and if it does, add "L'" before the name of the municipality
for row in range(len(data_df2)):
    if "(LES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "LES " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(LES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(LES)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(LOS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "LOS " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(LOS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(LOS)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(LAS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "LAS " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(LAS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(LAS)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(ES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "ES " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(ES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(ES)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(SES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "SES " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(SES)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(SES)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(ELS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "ELS " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(ELS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(ELS)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(A)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "A " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(A)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(A)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(AS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "AS " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(AS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(AS)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(O)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "O " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(O)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(O)", "")
    else: 
        continue

# %%
for row in range(len(data_df2)):
    if "(OS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = "OS " + data_df2['Municipality'][row]
    else: 
        continue

# check if a Municipality includes "(L')" and if it does, drop the "(L')"
for row in range(len(data_df2)):
    if "(OS)" in data_df2['Municipality'][row]:
        data_df2['Municipality'][row] = data_df2['Municipality'][row].replace("(OS)", "")
    else: 
        continue

# %%

data_df2['Municipality'] = data_df2['Municipality'].str.rstrip()

# %%


# %%
# from the orignal dataframe, create a new dataframe that has for row all the different owner, and for column the number of concession the own, the date of their last consession opening, the date of their 2 first concession termination, a list of thefrequency GHZ rounded of their concession, a list of the municipality of their concession
data_df3 = data_df2.groupby('Owner').agg({'Number of concession': 'max', 'Last opened concession': 'max', 'Concession termination': lambda x: list(x)[:2], 'Frequency GHZ rounded': lambda x: list(x), 'Municipality': lambda x: list(x)})
data_df3

# %%
# from data_df2 create a new dataframe with all the different municipality as rows, as column a list of the owner present in the municpality, the number of concession in the municpality, a list of the frequency GHZ rounded of the concession in the municpality, the number of owner in the municpality, the last concesion opening date in the municpality, and the next tow termination date in the municpality
data_df4 = data_df2.groupby('Municipality').agg({'Owner': lambda x: list(x), '# of concession in municipality': 'max', 'Frequency GHZ rounded': lambda x: list(x), '# of owner in municipality': 'max', 'Last opened concession': 'max', 'Concession termination': lambda x: list(x)[:2]})
data_df4

# %%
# import a list of all the existing municipality in spain
municipality = pd.read_csv('georef-spain-municipio-millesime.csv', sep=';')
# I want to only keep the Official Name Municiaplity from the municipality dataframe and I want to duplicate that column to have a new column called original name 
#municipality = municipality[['Official Name Municipality']]
municipality['Original Name Municipality'] = municipality['Official Name Municipality']
# in the official name municipality column, I want to remove all the - 
#municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('-', '')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('/', '')
#capitalize all the letter in the Official Name Municipality column
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.title()
# in the official name municipality column extract all the letter



# put all the Official Name Municipality in upper case
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.upper()
#remove all the accents from the Official Name Municipality and from the Municipality column in data_df2
#municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
municipality


# %%
municipality
# show me municipality where the offical name municipality contains HOSPITALET

#  in municipality dataframe column OFFICIAL NAME MUNICIPALITY repalce Á, É, Í, Ó, Ú, Ü by A, E, I, O, U, U

municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Á', 'A')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('À', 'A')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('É', 'E')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('È', 'E')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Í', 'I')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Ï', 'I')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Ó', 'O')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Ò', 'O')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Ú', 'U')
municipality['Official Name Municipality'] = municipality['Official Name Municipality'].str.replace('Ü', 'U')




# %%
# I want to verify that all the municipality in data_df2 are in the municipality['Official Name Municipality'] column
# I create a list of all the municipality in data_df2
municipality_list = data_df2['Municipality'].unique()
# I create a list of all the municipality in municipality['Official Name Municipality']
municipality_list2 = municipality['Official Name Municipality'].unique()
# I create a list of all the municipality in data_df2 that are not in municipality['Official Name Municipality']
municipality_list3 = [x for x in municipality_list if x not in municipality_list2]
# I create a list of all the municipality in municipality['Official Name Municipality'] that are not in data_df2
municipality_list4 = [x for x in municipality_list2 if x not in municipality_list]
# I create a list of all the municipality in data_df2 that are in municipality['Official Name Municipality']
municipality_list5 = [x for x in municipality_list if x in municipality_list2]
municipality_list3


# %%
# count the number of rows in data_df2 where municipality is in municipality_list3
data_df2[data_df2['Municipality'].isin(municipality_list3)].count()

# %%
# for all the municipality in data_df2 look for matching letters independently of their orders in municipality['Official Name Municipality'] and if there is a match, write the corresponding Original name municipality  in the Municipality column in data_df2
#for row in range(len(data_df2)):
 #   for row2 in range(len(municipality)):
  ##      if sorted(data_df2['Municipality'][row]) == sorted(municipality['Official Name Municipality'][row2]):
    #        data_df2['Municipality'][row] = municipality['Original Name Municipality'][row2]
     #   else:
      #      continue


# %%
# create a row in data_df2 called coordinates that is equal to the value of the Geo point column in municipality dataframe for the corresponding municipality
# create a column called coordinates in data_df2
data_df2['Coordinates'] = ''
data_df2["city_name"] = ''
for row in range(len(data_df2)):
    for row2 in range(len(municipality)):
        if data_df2['Municipality'][row] == municipality['Official Name Municipality'][row2]:
            data_df2['Coordinates'][row] = municipality['Geo Point'][row2]
            data_df2["city_name"][row] = municipality['Original Name Municipality'][row2]
        else:
            continue

# %%
municipality

# %%
# split coordinates into longitude and latitude
data_df2[['Latitude', 'Longitude']] = data_df2['Coordinates'].str.split(',', expand=True)

# %%
data_df2


# %%



# %%
# read a csv file
population = pd.read_csv('city_population.csv')
population
# from population dataframe I want to keep the column city and population
population = population[['city', 'population']]
# from population datframe I want to drop all the rows where the population is NaN
population = population.dropna()
# from population dataframe I want to drop all the rows where the population is less then 5000
population = population[population['population'] > 5000]
# rename the city column in population dataframe to Municipality
population = population.rename(columns={'city': 'Municipality'})
population

# %%
# create a new column in data_df2 called Population
data_df2['population'] = 0
# for all the municipality in data_df2 look for matching letters independently of their orders in population['Municipality'] and if there is a match, write the corresponding population in the Population column in data_df2
for row in range(len(data_df2)):
    for row2 in range(len(population)):
        if sorted(data_df2['city_name'][row]) == sorted(population['Municipality'][row2]):
            data_df2['population'][row] = population['population'][row2]
        else:
            continue
        



# %%
# if the population is larger than 300'000 then write large city in Popluation column in data_df2, if population is between 50'000 and 300'000 then write medium city, if population is between 10'000 and 50'000 then write small city, if population is between 5'000 and 10'000 write village, and if poplation is NaN or less than 5'000 then wirte small village
data_df2['Population'] = ''
for row in range(len(data_df2)):
    if data_df2['population'][row] > 300000:
        data_df2['Population'][row] = 'large city'
    elif data_df2['population'][row] > 50000:
        data_df2['Population'][row] = 'medium city'
    elif data_df2['population'][row] > 10000:
        data_df2['Population'][row] = 'small city'
    elif data_df2['population'][row] > 5000:
        data_df2['Population'][row] = 'village'
    elif data_df2['population'][row] < 5000:
        data_df2['Population'][row] = 'small village'    
    elif data_df2['population'][row] == 0:
        data_df2['Population'][row] = 'NA'    

# %%
# show me all the unique municipality in data_df2 where the Population is large city
data_df2[data_df2['Population'] == 'village']['Municipality'].unique()
data_df2

# %%s
# export data_df2 to a csv file and name it clean_sample_data_capstone_project
data_df2.to_csv('clean_sample_data_capstone_project.csv', index=False)


# %%
data_df2

# %%
# read a csv file
clean_sample_data_capstone_project = pd.read_csv('clean_sample_data_capstone_project.csv')

# %%



