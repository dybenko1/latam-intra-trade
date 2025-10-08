# Remember to install comtradeapicall package
import pandas as pd
import os 
import requests
from dotenv import load_dotenv

# Loading API Key
load_dotenv()
subscription_key = os.getenv("un_key")

# Defining parameters for make data request
typeCode='C' #Commodities data
freqCode='A' # Annual frequency
clCode='HS' # Harmonized System classification
countries_codes = ['84', '188', '222', '320', '340', '484', '558', '591', '32', '68', '76', '152', '170', '218', '600', '604', '858', '862'] # Selected LATAM countries
reporter = ",".join(countries_codes) 
flowCode="X" # Only Import or export at once


# Preparing request
request_url = f"https://comtradeapi.un.org/data/v1/get/{typeCode}/{freqCode}/{clCode}" # Obligatory parameters
headers = {'Ocp-Apim-Subscription-Key': subscription_key}
params = {
    "reporterCode": reporter,
    "period": 2023, # 2023 is the latest year now (october 2025) which has data for all selected countries
    "partnerCode": reporter + ",0", # Including the total trade of that country with the partner code '0'
    "partner2Code": "0", # Avoiding tripartite trade de-aggregation 
    "cmdCode": "TOTAL", # Focusing on all goods, not on a specific good given by its cmdCode
    "flowCode": flowCode, # Export or Import
    "customsCode": "C00", # We select all data from the Customs code filter
    "motCode" : 0, # We select all means of transportation (aggregated data)
    }

countries_dict = {
    84: "Belize",
    188: "Costa Rica",
    222: "El Salvador", 
    320: "Guatemala",
    340: "Honduras",
    484: "Mexico",
    558: "Nicaragua",
    591: "Panama",
    32: "Argentina",
    68: "Bolivia",
    76: "Brazil",
    152: "Chile",
    170: "Colombia",
    218: "Ecuador",
    600: "Paraguay",
    604: "Peru",
    858: "Uruguay",
    862: "Venezuela"
}


# Doing request (first for export data)
response = requests.get(url=request_url, params=params, headers=headers)
if response.status_code == 200:
    print("Retrieving export data... Succesful!\n")
else:
    print("Error retrieving data: {}".format(response.json()))

# Storing in DF
data = pd.DataFrame(response.json()["data"])

# Now doing it for imports
params["flowCode"] = "M"
response = requests.get(url=request_url, params=params, headers=headers)
if response.status_code == 200:
    print("Retrieving import data... Succesful!\n")
# Joining export and import data
data = pd.concat([data, pd.DataFrame(response.json()["data"])])


# Summarizing data by removing unnecessary columns 
required_cols = ["reporterCode", "flowCode", "partnerCode", "primaryValue"]
summary_data = data.loc[:, required_cols]

# Classifying partner countries as Latam or not Latam. Other deeper analysis can be done without aggregating data with this category
def find_country(valor):
    return countries_dict.get(valor, "Not LatinAmerica")

# Adding names to countries
summary_data["rep_country"] = summary_data["reporterCode"].apply(find_country)
summary_data["part_country"] = summary_data["partnerCode"].apply(find_country)

summary_data["NotLATAM"] = summary_data["part_country"] == "Not LatinAmerica"

# Adding import & exports 
summary_data = summary_data[['reporterCode', 'partnerCode',
       'rep_country', 'part_country', 'NotLATAM', 'primaryValue']].groupby(['reporterCode', 'partnerCode',
       'rep_country', 'part_country', 'NotLATAM']).sum().reset_index()

# Trade data of intra-Latinoamerica
summary_data.loc[summary_data["partnerCode"] != 0, ["rep_country", "primaryValue"]].groupby("rep_country").sum().sort_values(by="rep_country").to_clipboard()
summary_data.loc[summary_data["partnerCode"] != 0, ["rep_country", "primaryValue"]].groupby("rep_country").sum().sort_values(by="rep_country")

# Total Trade Data (latam + no latam) copied to clipboard to then use it to build the graph
summary_data.loc[summary_data["partnerCode"] == 0, ["rep_country", "primaryValue"]].sort_values(by="rep_country").to_clipboard()

## Checking Mexico Data to verify numbers
# summary_data.loc[summary_data["rep_country"] == "Mexico", ["partnerCode", "primaryValue"]].groupby("partnerCode").sum().sort_values(by="primaryValue", ascending=False)



# Caveats of this and further analysis.
#   Not using aggregate data: 
#   Country codes can have both individual countries or regions (e.g. 637: Center and North America, 129 Caribbean, etc.), hence summing trade data with all its trading partner codes may have duplicated data
#   This problem also occurs when summing by transport means, not all category codes are granular data
#   That was the reason why I choose to work with aggregate data with those variables and others like cmdCode
# 
# To compute total trade with no latam countries I subtract "Trade with Latam" from "Total Trade" 
